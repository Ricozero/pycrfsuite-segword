from itertools import chain
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelBinarizer
import pycrfsuite
from enum import IntEnum

def read_seg_file(filename):
    #处理语料库，使其符合格式
    #train file
    segfile = open(filename, encoding = 'utf-8')
    #formal train file
    formfile = open(filename + '.f', 'w+', encoding = 'utf-8')

    sents = segfile.readlines()
    #写成格式化临时文件
    for sent in sents:
        pre = 0 #前一个词的尾部，当前词的开始
        for cur, char in enumerate(sent):
            if char == ' ' and sent[cur - 1] != ' ':
                if pre + 1 == cur:
                    formfile.write(sent[pre] + ' S\n')
                else:
                    formfile.write(sent[pre] + ' B\n')
                    for i in range(pre + 1, cur - 1):
                        formfile.write(sent[i] + ' M\n')
                    formfile.write(sent[cur - 1] + ' E\n')
                pre = cur + 2
            else:
                continue
        #最后一个词，长度考虑回车；但最后一句没有回车
        if pre + 2 == len(sent) or pre + 1 == len(sent):
            if sent[pre] != '\n':
                formfile.write(sent[pre] + ' S\n')
        else:
            formfile.write(sent[pre] + ' B\n')
            for i in range(pre + 1, len(sent) - 2):
                formfile.write(sent[i] + ' M\n')
            formfile.write(sent[len(sent) - 2] + ' E\n')
        formfile.write('\n')

    segfile.close()

    #读取格式化训练文件
    formfile.seek(0, 0)
    lines = formfile.readlines()
    train_sents = []
    train_sents.append([])
    i = 0
    for line in lines:
        if line =='\n':
            if len(train_sents[i]) > 0:
                train_sents.append([])
                i += 1
        else:
            train_sents[i].append((line[0], line[2]))
    formfile.close()
    return train_sents

def ispunct(char):
    punct_cn = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.'
    punct_en = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    if char in punct_cn or char in punct_en:
        return True
    else:
        return False

def word2features(sent, i):
    word = sent[i][0]
    features = [
        'bias',
        'word=' + word,
        'word.isdigit=%s' % word.isdigit(),
        'word.ispunct=%s' % ispunct(word)
    ]
    if i > 0:
        word = sent[i-1][0]
        features.extend([
            '-1:word=' + word,
            '-1:word.isdigit=%s' % word.isdigit(),
            '-1:word.ispunct=%s' % ispunct(word)
        ])
        if i > 1:
            word = sent[i-2][0]
            features.extend([
                '-2:word=' + word,
                '-2:word.isdigit=%s' % word.isdigit(),
                '-2:word.ispunct=%s' % ispunct(word)
            ])
    else:
        features.append('BOS')

    if i < len(sent)-1:
        word = sent[i+1][0]
        features.extend([
            '+1:word=' + word,
            '+1:word.isdigit=%s' % word.isdigit(),
            '+1:word.ispunct=%s' % ispunct(word)
        ])
        if i < len(sent)-2:
            word = sent[i+2][0]
            features.extend([
                '+2:word=' + word,
                '+2:word.isdigit=%s' % word.isdigit(),
                '+2:word.ispunct=%s' % ispunct(word)
            ])
    else:
        features.append('EOS')

    return features

def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def sent2labels(sent):
    return [label for token, label in sent]

def sent2tokens(sent):
    return [token for token, label in sent]

def train(sents):
    X_train = [sent2features(s) for s in sents]
    y_train = [sent2labels(s) for s in sents]

    trainer = pycrfsuite.Trainer(verbose=False)

    #zip函数可以使得X和y的每一个元素按顺序组成元组
    for xseq, yseq in zip(X_train, y_train):
        trainer.append(xseq, yseq)

    trainer.set_params({
        'c1': 1.0,   # coefficient for L1 penalty
        'c2': 1e-3,  # coefficient for L2 penalty
        'max_iterations': 50,  # stop earlier

        # include transitions that are possible, but not observed
        'feature.possible_transitions': True
    })
    #trainer.params()
    trainer.train('trainer')
    return trainer

def bmes_classification_report(y_true, y_pred):
    lb = LabelBinarizer()
    y_true_combined = lb.fit_transform(list(chain.from_iterable(y_true)))
    y_pred_combined = lb.transform(list(chain.from_iterable(y_pred)))

    tagset = set(lb.classes_) - {'\n'}
    tagset = sorted(tagset)
    class_indices = {cls: idx for idx, cls in enumerate(lb.classes_)}

    return classification_report(
        y_true_combined,
        y_pred_combined,
        labels = [class_indices[cls] for cls in tagset],
        target_names = tagset,
    )

def print_transitions(trans_features):
    for (label_from, label_to), weight in trans_features:
        print("%-6s -> %-7s %0.6f" % (label_from, label_to, weight))

def print_state_features(state_features):
    for (attr, label), weight in state_features:
        print("%0.6f %-6s %s" % (weight, label, attr))