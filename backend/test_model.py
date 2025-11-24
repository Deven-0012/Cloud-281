import tensorflow as tf
model = tf.keras.models.load_model(
    "/Users/devendesai/281/Final project/model/my_yamnet_human_model_compatible.keras",
    compile=False
)
model.summary()
