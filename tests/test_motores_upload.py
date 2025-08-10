import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from api.models import Motor, User


@pytest.mark.django_db
class TestMotorUpload:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_authenticate(user=self.user)
        self.motor = Motor.objects.create(
            codigo='MTR001',
            potencia='5HP',
            tipo='AC',
            rpm='1500',
            brida='B3',
            anclaje='Base',
            creado_por=self.user
        )

    def test_upload_motor_image_valid(self):
        url = reverse('motor-upload-foto', args=[self.motor.id])
        image_file = SimpleUploadedFile(
            "test_image.jpg", b"file_content_here", content_type="image/jpeg"
        )

        response = self.client.post(
            url,
            {'file': image_file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_upload_motor_plano_valid_pdf(self):
        url = reverse('motor-upload-plano', args=[self.motor.id])
        pdf_file = SimpleUploadedFile(
            "test_plano.pdf", b"%PDF-1.4 test pdf content", content_type="application/pdf"
        )
        response = self.client.post(
            url,
            {'file': pdf_file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'plano_url' in response.data

    def test_upload_motor_plano_invalid_extension(self):
        url = reverse('motor-upload-plano', args=[self.motor.id])
        bad_file = SimpleUploadedFile(
            "bad_file.exe", b"Not a PDF", content_type="application/octet-stream"
        )
        response = self.client.post(
            url,
            {'file': bad_file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_motor_plano_invalid_content(self):
        url = reverse('motor-upload-plano', args=[self.motor.id])
        fake_pdf = SimpleUploadedFile(
            "fake.pdf", b"This is not PDF", content_type="application/pdf"
        )
        response = self.client.post(
            url,
            {'file': fake_pdf},
            format='multipart'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
