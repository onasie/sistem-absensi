from keras.models import load_model
from keras.layers import Input,Lambda, Dense, Conv2D, MaxPooling2D, Flatten, Dropout
from keras.models import Model, Sequential
from tensorflow.keras.optimizers import RMSprop
from keras import backend as K
import os
import numpy as np


def create_shared_network(input_shape):
	model = Sequential (name='Shared_Conv_Network')
	model.add(Conv2D(filters=64, kernel_size=(3,3), activation='relu', input_shape = input_shape))
	model.add(MaxPooling2D())
	model.add(Conv2D(filters=32, kernel_size=(3,3), activation='relu'))
	model.add(MaxPooling2D())
	model.add(Dropout(0.2))
	model.add(Flatten())
	model.add(Dense(units=128, activation='sigmoid'))
	return model

def euclidean_distance(vectors):
	vector1, vector2 = vectors
	sum_square = K.sum(K.square(vector1-vector2), axis=1, keepdims=True)
	return K.sqrt(K.maximum(sum_square, K.epsilon()))

def sigmoid(x):
	return (1/(1+np.exp(-x)))

def contrastive_loss(Y_true, D):
	margin = 1
	return K.mean(Y_true * K.square(D) + (1-Y_true) * K.maximum((margin-D),0))

def accuracy(Y_true, Y_pred):
	return K.mean(K.equal(Y_true, K.cast(Y_pred < 0.5, Y_true.dtype)))

def predict_embedding(images):
	K.clear_session()
	images = np.array(images)
		
	images = images.reshape(images.shape[0],96,96,1)
	print(images.shape)

	input_shape = (96,96,1)
	shared_network = create_shared_network(input_shape)
	input_top = Input(shape=input_shape)
	input_bottom = Input(shape=input_shape)
	output_top = shared_network(input_top)
	output_bottom = shared_network(input_bottom)
	distance = Lambda(euclidean_distance, output_shape=(1,))([output_top, output_bottom])
	model = Model(inputs=[input_top, input_bottom], outputs=distance)
	model.summary()
	opt = RMSprop(lr=0.0005)
	model.compile(loss=contrastive_loss, optimizer=opt, metrics=[accuracy])

	model_filepath = os.path.join(os.getcwd(),'Siamese','Siamese_2CNN_F.h5' )
	# model = load_model(model_filepath, custom_objects = {'contrastive_loss':contrastive_loss,
	                                                     # 'euclidean_distance':euclidean_distance})
	siamese_model = load_model(model_filepath, compile=False)
	sourceModel= siamese_model.get_layer('Shared_Conv_Network')
	targetModel = create_shared_network(input_shape)

	for l_tg, l_sr in zip(targetModel.layers, sourceModel.layers):
		wk0 = l_sr.get_weights()
		l_tg.set_weights(wk0)


	embedding = []
	model.load_weights(model_filepath)
	for i in range(0, images.shape[0]):
		img1 = np.expand_dims(images[i],axis=0)
		a = targetModel.predict(img1)
		# a=sigmoid(a)
		embedding.append(a)
		
	print("Hasil EMBEDDING: ", np.array(embedding))
	return np.array(embedding)

def get_model():
	input_shape = (96,96,1)
	
	model_filepath = os.path.join(os.getcwd(),'Siamese','Siamese_2CNN_F.h5' )
	siamese_model = load_model(model_filepath, compile=False)
	sourceModel= siamese_model.get_layer('Shared_Conv_Network')
	targetModel = create_shared_network(input_shape)

	for l_tg, l_sr in zip(targetModel.layers, sourceModel.layers):
		wk0 = l_sr.get_weights()
		l_tg.set_weights(wk0)

	
	return targetModel
