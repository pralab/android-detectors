# Android Malware Detectors
End-to-end implementation of ML-based Android malware detectors.

## Available Detectors
- **DREBIN** from Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014. [[paper]](https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf)
- **SecSVM** from Demontis et al. "Yes, machine learning can be more secure! a case study
     on android malware detection." IEEE TDSC 2017. [[paper]](https://arxiv.org/abs/1704.08996)
- A **BaseDREBIN** class is also provided, allowing to easily and efficiently train any classifier on the DREBIN feature set by extending a few methods.

Pre-trained models (on the [ELSA dataset](https://benchmarks.elsa-ai.eu/?ch=6&com=downloads)) can also be downloaded from Drive:
- [DREBIN](https://drive.google.com/drive/folders/1EkOpO88p2FOW1NL5H_AbB4EKgfHeynIA?usp=sharing)
- [SecSVM](https://drive.google.com/drive/folders/11AY4ZQH0pExjEhCvFo3J6FpojnR2zWXE?usp=sharing)

The downloaded files must be placed in the `pretrained` folder.
