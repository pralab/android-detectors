import os


def generate_filepath(apk, ext, out_dir):
    filename = os.path.splitext(os.path.basename(apk))[0] + "." + ext
    return os.path.join(out_dir, filename)
