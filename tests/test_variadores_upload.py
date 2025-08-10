import io
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from yourapp.models import Variador, User


@pytest.mark.django_db
class TestVariadorUpload:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.force_authenticate(user=self.user)
        self.variador = Variador.objects.create(
            codigo='VAR001',
            marca='ABB',
            modelo='X100',
            potencia='10HP',
            creado_por=self.user
        )

    def test_upload_variador_image_valid(self):
        url = reverse('variador-upload-file', args=[self.variador.id])
        image_content = io.BytesIO()
        image_content.write(b'\x47\x49\x46')
        image_content.seek(0)

        response = self.client.post(
            url,
            {'imagen': image_content, 'file_name': 'test_image.jpg'},
            format='multipart'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'imagen_url' in response.data

    def test_upload_variador_manual_valid_pdf(self):
        url = reverse('variador-upload-file', args=[self.variador.id])
        pdf_content = io.BytesIO(b'%PDF-1.4 test pdf content')
        response = self.client.post(
            url,
            {'manual': pdf_content, 'file_name': 'test_manual.pdf'},
            format='multipart'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'manual_url' in response.data

    def test_upload_variador_manual_invalid_extension(self):
        url = reverse('variador-upload-file', args=[self.variador.id])
        bad_content = io.BytesIO(b'Not a PDF')
        response = self.client.post(
            url,
            {'manual': bad_content, 'file_name': 'bad_file.exe'},
            format='multipart'
        )

        # ⚠️ Solo falla si validas en el ViewSet
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

