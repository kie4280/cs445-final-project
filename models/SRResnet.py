from turtle import forward
from typing import List
from tensorflow import Module, Variable, Tensor
from tensorflow.keras import layers, activations, Model
import logging
import tensorflow as tf


class ResBlock(layers.Layer):
    def __init__(self, trainable=True, name=None, dtype=None, dynamic=False, **kwargs):
        super().__init__(trainable, name, dtype, dynamic, **kwargs)
        self.conv1 = layers.Conv2D(64, 3, padding='same')
        self.conv2 = layers.Conv2D(64, 3, padding='same')
        self.bn1 = layers.BatchNormalization()
        self.bn2 = layers.BatchNormalization()
        self.prelu = layers.PReLU()

    def call(self, x: Tensor) -> Tensor:
        y = self.conv1(x)
        y = self.bn1(y)
        y = self.prelu(y)
        y = self.conv2(y)
        y = self.bn2(y)
        return x + y


class SubPixConv2D(layers.Layer):
    def __init__(self, scale: int = 2, trainable=True, name=None, dtype=None, dynamic=False, **kwargs):
        super().__init__(trainable, name, dtype, dynamic, **kwargs)
        self.scale = scale
        self.conv1 = layers.Conv2D(64*scale*2, 3)
        self.prelu = layers.PReLU()

    def call(self, x: Tensor):
        y = self.conv1(x)
        y = tf.nn.depth_to_space(y, self.scale)
        y = self.prelu(y)
        return y


class SRResnet(Model):
    def __init__(self, B: int = 16, name=None):
        super().__init__(name)
        self.blocks: List = []
        self.B: int = B
        self.up1 = SubPixConv2D(2)
        self.up2 = SubPixConv2D(2)
        self.conv1 = layers.Conv2D(64, 3, padding='same')
        self.conv2 = layers.Conv2D(64, 3, padding='same')
        self.conv_compress = layers.Conv2D(3, 1)
        self.prelu = layers.PReLU()
        self.bn = layers.BatchNormalization()
        for i in range(B):
            self.blocks.append(ResBlock())

    def call(self, x: Tensor) -> Tensor:
        y = self.conv1(x)
        y = self.prelu(y)
        x = tf.identity(y)
        for i in range(self.B):
            y = self.blocks[i](y)
        y = self.conv2(y)
        y = self.bn(y)
        y = y + x
        y = self.up1(y)
        y = self.up2(y)
        y = self.conv_compress(y)
        return y


def test():
    physical_devices = tf.config.list_physical_devices('GPU')
    try:
        tf.config.experimental.set_memory_growth(physical_devices[0], True)
    except:
    # Invalid device or cannot modify virtual devices once initialized.
        pass
    imsize = (1, 2000, 2000, 3)
    tf.random.set_seed(0)
    x = tf.random.uniform(imsize)
    with tf.device("gpu"):
        sr = SRResnet()
        y:Tensor = sr(x)
    # print(y)

    logging.basicConfig(filename='SRResnet.log', encoding='utf-8', level=logging.DEBUG, filemode='a+')
    logging.info(str(y))


if __name__ == "__main__":
    test()