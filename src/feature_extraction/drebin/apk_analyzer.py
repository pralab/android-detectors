import json
import re
import zipfile
from xml.dom import minidom
import os
import time
import lxml
import lxml.etree
from androguard.core.bytecodes import apk
from androguard.core.bytecodes import dvm
import validators
import hashlib

"""
Part of the following code was taken from:
https://github.com/MLDroid/drebin
"""


def process_apk(apk_file, features_out_dir, logger):

    start_time = time.time()

    try:
        logger.debug(f"start to process {apk_file} ...")
        app_obj = apk.APK(apk_file)
        req_permissions, activities, services, providers, \
            receivers, hardware_components, intent_filters = \
            get_from_xml(apk_file, app_obj, logger)
        data_dictionary = {
            "req_permissions": req_permissions, "activities": activities,
            "services": services, "providers": providers,
            "receivers": receivers, "features": hardware_components,
            "intent_filters": intent_filters}

        used_permissions, restricted_apis, suspicious_apis, url_domain = \
            get_from_instructions(app_obj, logger)
        data_dictionary.update({
            "used_permissions": used_permissions, "api_calls": restricted_apis,
            "suspicious_calls": suspicious_apis, "urls": url_domain})

        data_dictionary = {k: list(v) for k, v in data_dictionary.items()}

        if features_out_dir is not None:
            filename_data = os.path.join(
                features_out_dir,
                os.path.splitext(os.path.basename(apk_file))[0] + ".json")
            with open(filename_data, "w") as f:
                json.dump(data_dictionary, f)

    except Exception as e:
        final_time = time.time()
        logger.debug(e)
        logger.debug(f"{apk_file} processing failed in "
                     f"{final_time - start_time}s...")
        return None
    else:
        final_time = time.time()
        logger.debug(f"{apk_file} processed successfully in "
                     f"{final_time - start_time}s")
        return [f"{k}::{v}" for k in data_dictionary for v in
                data_dictionary[k] if data_dictionary[k]]


def get_from_xml(apk_file, app_obj, logger):

    filename_xml = f"{apk_file}.xml"

    req_permissions = set()
    activities = set()
    services = set()
    providers = set()
    receivers = set()
    hardware_components = set()
    intent_filters = set()
    try:
        apk_file = os.path.abspath(apk_file)
        with open(filename_xml, "w") as f:
            f.write(lxml.etree.tostring(app_obj.xml['AndroidManifest.xml'],
                                        pretty_print=True).decode())
    except Exception as e:
        logger.debug(e)
        logger.debug(f"error while reading {apk_file} AndroidManifest.xml")
        if os.path.exists(filename_xml):
            os.remove(filename_xml)
        return
    try:
        with open(filename_xml, "r") as f:
            dom = minidom.parse(f)

        dom_collection = dom.documentElement

        dom_permission = dom_collection.getElementsByTagName("uses-permission")
        list(map(
            lambda permission: req_permissions.add(
                permission.getAttribute("android:name")),
            (permission for permission in dom_permission
             if permission.hasAttribute("android:name"))))

        list(map(
            lambda activity: activities.add(
                activity.getAttribute("android:name")),
            (activity for activity in
             dom_collection.getElementsByTagName("activity")
             if activity.hasAttribute("android:name"))))

        list(map(
            lambda service: services.add(service.getAttribute("android:name")),
            (service for service in
             dom_collection.getElementsByTagName("service")
             if service.hasAttribute("android:name"))))

        list(map(
            lambda provider: providers.add(
                provider.getAttribute("android:name")),
            (provider for provider in
             dom_collection.getElementsByTagName("provider")
             if provider.hasAttribute("android:name"))))

        list(map(
            lambda receiver: receivers.add(
                receiver.getAttribute("android:name")),
            (receiver for receiver in
             dom_collection.getElementsByTagName("receiver")
             if receiver.hasAttribute("android:name"))))

        list(map(
            lambda hardware_component: hardware_components.add(
                hardware_component.getAttribute("android:name")),
            (hardware_component for hardware_component in
             dom_collection.getElementsByTagName("uses-feature")
             if hardware_component.hasAttribute("android:name"))))

        list(map(
            lambda action: intent_filters.add(
                action.getAttribute("android:name")),
            (action for action in dom_collection.getElementsByTagName("action")
             if action.hasAttribute("android:name"))))

    except Exception as e:
        logger.debug(e)
        return req_permissions, activities, services, providers, receivers, \
            hardware_components, intent_filters
    finally:
        if os.path.exists(filename_xml):
            os.remove(filename_xml)
        return req_permissions, activities, services, providers, receivers, \
            hardware_components, intent_filters


def get_from_instructions(app_obj, logger):

    app_sdk = app_obj.get_effective_target_sdk_version()
    # FIXME: hardcoded for now
    if app_sdk > 30:
        use_mapping = 30
    elif app_sdk < 23:
        use_mapping = "older"
    else:
        use_mapping = app_sdk

    with open(os.path.join(os.path.dirname(__file__),
                           f"resources/perm_mapping_{use_mapping}.json"),
              "r") as f:
        perm_mapping = json.load(f)

    api_mapping = {api: perm for perm, apis in perm_mapping.items()
                   for api in apis}

    used_permissions = set()
    restricted_apis = set()
    suspicious_apis = set()
    url_domains = set()
    android_suspicious_apis = {
        "getExternalStorageDirectory", "getSimCountryIso", "execHttpRequest",
        "sendTextMessage", "getSubscriberId", "getDeviceId", "getPackageInfo",
        "getSystemService", "getWifiState", "setWifiEnabled",
        "setWifiDisabled", "getCellLocation", "getNetworkCountryIso",
        "SystemClock/uptimeMillis", "getCellSignalStrength", "Cipher",
        "system/bin/su", "android/os/Exec", "adb_enabled", "Base64",
        "Lorg/apache/http/client/methods/HttpPost",
        "Ljava/net/HttpURLconnection;->setRequestMethod(Ljava/lang/String;)",
        "Ljava/net/HttpURLconnection",
        "Ljava/io/IOException;->printStackTrace", "Ljava/lang/Runtime;->exec",
        "Ljava/lang/System;->loadLibrary", "Ljava/lang/System;->load",
        "Ldalvik/system/DexClassLoader;", "Ldalvik/system/SecureClassLoader;",
        "Ldalvik/system/PathClassLoader;", "Ldalvik/system/URLClassLoader;",
        "Ldalvik/system/BaseDexClassLoader;",
        "Landroid/telephony/SmsMessage;->getMessageBody",
        "Landroid/os/Build;->BRAND:Ljava/lang/String",
        "Landroid/os/Build;->DEVICE:Ljava/lang/String",
        "Landroid/os/Build;->MODEL:Ljava/lang/String",
        "Landroid/os/Build;->PRODUCT:Ljava/lang/String",
        "Landroid/os/Build;->FINGERPRINT:Ljava/lang/String"
    }

    api_pattern = re.compile("L(.*)" + re.escape("("))
    url_pattern = re.compile(
        "http[s]?://([\w\d-]+\.)*[\w-]+[\.\:]\w+([\/\?\=\&\#.]?[\w-]+)*\/?")
    ip_pattern = re.compile(
        "(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})")
    # TODO: add ipv6?

    def process_api(signature):
        try:
            if signature in api_mapping:
                used_permissions.add(api_mapping[signature])
                restricted_apis.add(signature)
        except Exception as inst_match_err:
            logger.debug(f"instruct error: {inst_match_err}")

    def parse_url(instruction):
        # URLs are obfuscated with md5 hash to avoid releasing sensitive data
        url = re.search(url_pattern, instruction)
        if url:  # we could validate urls but we may miss special f-strings
            url_hash = hashlib.md5(
                url.group().encode()).hexdigest()
            url_domains.add(url_hash)
        ip = re.search(ip_pattern, instruction)
        if ip and validators.ipv4(ip.group()):
            ip_hash = hashlib.md5(
                ip.group().encode()).hexdigest()
            url_domains.add(ip_hash)

    for dex_name in app_obj.get_dex_names():
        try:
            dex = app_obj.get_file(dex_name)
        except zipfile.BadZipfile:
            continue
        try:
            dx = dvm.DalvikVMFormat(dex)
            for method in (m for m in dx.get_methods() if
                           m.get_code() is not None):
                byte_code = method.get_code().get_bc()
                for instruction in byte_code.get_instructions():
                    instruction = instruction.get_output()
                    if instruction is None:
                        continue
                    suspicious_apis.update(
                        {e for e in android_suspicious_apis
                         if e in instruction})
                    signature = re.findall(api_pattern, instruction)
                    if len(signature) != 0:
                        process_api(signature[0])
                    parse_url(instruction)
        except ValueError as e:
            if str(e).startswith("This is not a DEX file!"):
                continue
            else:
                raise e

    return used_permissions, restricted_apis, suspicious_apis, url_domains
