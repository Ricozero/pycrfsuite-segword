# 基于CRF的分词

中文信息处理自动分词作业，因为不可以使用CRF++，最后用了pycrfsuite.

## 文件说明

- src
  - crftest.py：crfsuite自带示例
  - main.py：训练、测试、评估、输出一体化
  - segword.py：核心函数
  - test.py：仅包含测试和评估、输出
- test
  - 已分词的测试集
- train
  - 已分词的训练集

注：测试集和训练集中，.utf8格式的文件来自于icwb2-data