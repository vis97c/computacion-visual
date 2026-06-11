import os
import sys
import unittest
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app

class MicroplasticsApiTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_model_info_endpoint(self):
        """Tests that GET /api/model-info returns the model parameters."""
        response = self.app.get('/api/model-info')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('classes', data)
        self.assertIn('mean_accuracy', data)
        self.assertIn('feature_importances', data)
        self.assertIn('confusion_matrix', data)

    def test_stats_endpoint(self):
        """Tests that GET /api/stats returns statistics from Excel."""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_samples', data)
        self.assertIn('class_distribution', data)
        self.assertIn('agreement_rate', data)
        self.assertIn('annotator_counts', data)

    def test_predict_endpoint_missing_file(self):
        """Tests that POST /api/predict without a file returns 400."""
        response = self.app.post('/api/predict')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_predict_with_sample_image(self):
        """Tests predicting with a physical image file from the dataset."""
        # Find a physical TIFF image that exists
        sample_path = "Ceroplastic/P2T2M1-A/P2T1M1-A-1.tif"
        if not os.path.exists(sample_path):
            self.skipTest("Sample image not found for prediction test.")
            
        with open(sample_path, 'rb') as f:
            img_bytes = f.read()
            
        response = self.app.post(
            '/api/predict',
            data={'file': (io.BytesIO(img_bytes), 'P2T1M1-A-1.tif')},
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('annotated_image', data)
        self.assertIn('particles', data)
        self.assertIn('counts', data)
        self.assertIn('total_detected', data)
        self.assertIn('total_microplastics', data)

if __name__ == '__main__':
    unittest.main()
