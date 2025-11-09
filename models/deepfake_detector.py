"""
AI-Powered Deepfake Detector using CNN and RNN
Implements MesoNet-4 (CNN) architecture combined with LSTM (RNN) for temporal analysis
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.layers import LSTM, TimeDistributed, Reshape
from tensorflow.keras.optimizers import Adam
import numpy as np
import os


class DeepfakeDetector:
    """
    Hybrid CNN-RNN model for deepfake detection
    - CNN (MesoNet-4): Extracts spatial features from images
    - RNN (LSTM): Analyzes temporal patterns and sequences
    """
    
    def __init__(self, input_shape=(256, 256, 3), weights_path=None):
        self.input_shape = input_shape
        self.weights_path = weights_path
        self.model = None
        self.build_model()
        
        if weights_path and os.path.exists(weights_path):
            self.load_weights(weights_path)
    
    def build_mesonet_cnn(self, input_tensor):
        """
        MesoNet-4 CNN architecture for spatial feature extraction
        Optimized for detecting mesoscopic properties of deepfakes
        """
        # First convolutional block
        x = Conv2D(8, (3, 3), padding='same', activation='relu')(input_tensor)
        x = BatchNormalization()(x)
        x = MaxPooling2D(pool_size=(2, 2), padding='same')(x)
        
        # Second convolutional block
        x = Conv2D(8, (5, 5), padding='same', activation='relu')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D(pool_size=(2, 2), padding='same')(x)
        
        # Third convolutional block
        x = Conv2D(16, (5, 5), padding='same', activation='relu')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D(pool_size=(2, 2), padding='same')(x)
        
        # Fourth convolutional block
        x = Conv2D(16, (5, 5), padding='same', activation='relu')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D(pool_size=(4, 4), padding='same')(x)
        
        return x
    
    def build_model(self):
        """
        Build the complete CNN-RNN hybrid model
        """
        # Input layer
        input_layer = Input(shape=self.input_shape)
        
        # CNN feature extraction (MesoNet-4)
        cnn_features = self.build_mesonet_cnn(input_layer)
        
        # Flatten CNN output
        flattened = Flatten()(cnn_features)
        
        # Reshape for LSTM (treating features as sequence)
        # This allows the LSTM to learn temporal patterns in feature space
        lstm_input = Reshape((16, -1))(flattened)
        
        # LSTM layers for temporal analysis
        lstm_out = LSTM(64, return_sequences=True)(lstm_input)
        lstm_out = Dropout(0.5)(lstm_out)
        lstm_out = LSTM(32, return_sequences=False)(lstm_out)
        lstm_out = Dropout(0.5)(lstm_out)
        
        # Dense layers for classification
        dense = Dense(16, activation='relu')(lstm_out)
        dense = Dropout(0.5)(dense)
        
        # Output layer (binary classification: real vs fake)
        output = Dense(1, activation='sigmoid')(dense)
        
        # Create model
        self.model = Model(inputs=input_layer, outputs=output)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        return self.model
    
    def predict(self, image):
        """
        Predict if an image is real or fake
        
        Args:
            image: Preprocessed image array (256x256x3)
            
        Returns:
            dict: {
                'prediction': 'real' or 'fake',
                'confidence': float (0-1),
                'fake_probability': float (0-1),
                'real_probability': float (0-1)
            }
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")
        
        # Ensure image has batch dimension
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        # Get prediction
        fake_prob = float(self.model.predict(image, verbose=0)[0][0])
        real_prob = 1.0 - fake_prob
        
        # Determine prediction
        prediction = 'fake' if fake_prob > 0.5 else 'real'
        confidence = max(fake_prob, real_prob)
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'fake_probability': fake_prob,
            'real_probability': real_prob
        }
    
    def predict_batch(self, images):
        """
        Predict multiple images at once
        
        Args:
            images: Array of preprocessed images
            
        Returns:
            list: List of prediction dictionaries
        """
        if self.model is None:
            raise ValueError("Model not built or loaded")
        
        predictions = self.model.predict(images, verbose=0)
        
        results = []
        for pred in predictions:
            fake_prob = float(pred[0])
            real_prob = 1.0 - fake_prob
            prediction = 'fake' if fake_prob > 0.5 else 'real'
            confidence = max(fake_prob, real_prob)
            
            results.append({
                'prediction': prediction,
                'confidence': confidence,
                'fake_probability': fake_prob,
                'real_probability': real_prob
            })
        
        return results
    
    def save_weights(self, path):
        """Save model weights"""
        if self.model:
            self.model.save_weights(path)
            print(f"Model weights saved to {path}")
    
    def load_weights(self, path):
        """Load model weights"""
        if self.model and os.path.exists(path):
            self.model.load_weights(path)
            print(f"Model weights loaded from {path}")
        else:
            print(f"Warning: Weights file not found at {path}")
    
    def train(self, train_data, train_labels, validation_data=None, epochs=50, batch_size=32):
        """
        Train the model
        
        Args:
            train_data: Training images
            train_labels: Training labels (0=real, 1=fake)
            validation_data: Tuple of (val_images, val_labels)
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        if self.model is None:
            raise ValueError("Model not built")
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=10,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if validation_data else 'loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]
        
        # Train
        history = self.model.fit(
            train_data,
            train_labels,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def get_model_summary(self):
        """Get model architecture summary"""
        if self.model:
            return self.model.summary()
        return None


class SimpleDeepfakeDetector:
    """
    Simplified CNN-only model for faster inference
    Uses a lightweight architecture for real-time detection
    """
    
    def __init__(self, input_shape=(256, 256, 3)):
        self.input_shape = input_shape
        self.model = self.build_simple_model()
    
    def build_simple_model(self):
        """Build a simple CNN model"""
        model = models.Sequential([
            # Input layer
            Input(shape=self.input_shape),
            
            # Convolutional blocks
            Conv2D(32, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D((2, 2)),
            Dropout(0.25),
            
            Conv2D(64, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D((2, 2)),
            Dropout(0.25),
            
            Conv2D(128, (3, 3), activation='relu', padding='same'),
            BatchNormalization(),
            MaxPooling2D((2, 2)),
            Dropout(0.25),
            
            # Dense layers
            Flatten(),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def predict(self, image):
        """Predict if image is real or fake"""
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        fake_prob = float(self.model.predict(image, verbose=0)[0][0])
        real_prob = 1.0 - fake_prob
        prediction = 'fake' if fake_prob > 0.5 else 'real'
        confidence = max(fake_prob, real_prob)
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'fake_probability': fake_prob,
            'real_probability': real_prob
        }


# Initialize pre-trained model with synthetic weights for demo
def initialize_pretrained_model():
    """
    Initialize a model with pre-trained weights
    In production, this would load actual trained weights
    """
    detector = DeepfakeDetector()
    
    # For demo purposes, we'll use the model as-is
    # In production, you would load actual trained weights:
    # detector.load_weights('path/to/trained/weights.h5')
    
    return detector
