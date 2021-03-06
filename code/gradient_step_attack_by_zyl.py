import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch.autograd.gradcheck import zero_gradients
import numpy as np
from models import TwoLayerFC, ThreeLayerConvNet, AlexNet
import matplotlib.pyplot as plt


def unpickle(file):
    import pickle
    with open(file, 'rb') as fo:
        pickle_dict = pickle.load(fo, encoding='latin1')
    return pickle_dict


# load test images
test_dict = unpickle('cifar-10-batches-py/test_batch')
test_X = test_dict.get('data')
test_Y = test_dict.get('labels')
label_names = unpickle('cifar-10-batches-py/batches.meta').get('label_names')
test_X = np.array(test_X).reshape(10000, 1, 3, 32, 32).astype(np.float32) / 255.0
test_Y = np.array(test_Y).reshape(10000)

# load models
filename = 'model_set/Two_layer_FC_'
model_0 = torch.load(filename+'1.pkl')
model_1 = torch.load(filename+'2.pkl')
loss = nn.CrossEntropyLoss()

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)
print(torch.cuda.get_device_name(0))

classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse',
           'ship', 'truck')


def show_result(img):
    model_0.to(device).eval()
    model_1.to(device).eval()
    img = torch.from_numpy(img).to(device)
    res_0 = F.softmax(model_0(img), dim=1).data
    print('Res_0:')
    print(res_0)
    res_0 = res_0.max(1)
    res_1 = F.softmax(model_1(img), dim=1).data
    print('Res_1:')
    print(res_1)
    res_1 = res_1.max(1)
    img = img.cpu().numpy().reshape(3, 32, 32).transpose(1, 2, 0)
    plt.suptitle('images')
    plt.subplot(1, 2, 1), plt.title('model_0 '+classes[res_0[1].cpu().numpy()[0]]+' Prob='+str(res_0[0].cpu().numpy()[0])[0:5])
    plt.imshow(img), plt.axis('off')
    plt.subplot(1, 2, 2), plt.title('model_1 '+classes[res_1[1].cpu().numpy()[0]]+' Prob='+str(res_1[0].cpu().numpy()[0])[0:5])
    plt.imshow(img), plt.axis('off')
    plt.show()


def nontargeted_attack(img, steps, step_lr, eps):
    model_0.to(device).eval()
    img = torch.from_numpy(img).to(device)
    label = model_0(img).data.max(1)[1]
    x, y = Variable(img, requires_grad=True).to(device), Variable(label).to(device)
    for step in range(steps):
        # print('No.%d' % (step))
        zero_gradients(x)
        out = model_0(x)
        y.data = out.data.max(1)[1]
        # print(y.data)
        _loss = loss(out, y)
        _loss.backward()
        normed_grad = step_lr * torch.sign(x.grad.data)
        step_adv = x.data + normed_grad
        adv = step_adv - img
        adv = torch.clamp(adv, -eps, eps)
        result = img + adv
        result = torch.clamp(result, 0.0, 1.0)
        x.data = result
    return result.cpu(), adv.cpu()


def targeted_attack(img, steps, step_lr, eps, label):
    model_0.to(device).eval()
    img = torch.from_numpy(img).to(device)
    label = torch.Tensor([label]).long().to(device)
    x, y = Variable(img, requires_grad=True).to(device), Variable(label).to(device)
    for step in range(steps):
        zero_gradients(x)
        out = model_0(x)
        _loss = loss(out, y)
        _loss.backward()
        normed_grad = step_lr * torch.sign(x.grad.data)
        step_adv = x.data - normed_grad
        adv = step_adv - img
        adv = torch.clamp(adv, -eps, eps)
        result = img + adv
        result = torch.clamp(result, 0.0, 1.0)
        x.data = result
    return result.cpu(), adv.cpu()


att_img = test_X[0]
show_result(att_img)
att_result, att_delta = targeted_attack(att_img, steps=50, step_lr=0.001, eps=0.1, label=0)
show_result(att_result.numpy())
