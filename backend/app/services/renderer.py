import pymupdf
import io
from app.storage import minio_client
from app.config import settings

class PDFRenderer:
    def __init__(self):
        self.bucket = settings.MINIO_PAGES_BUCKET

    def render_document_with_metadata(self, document_id: str, pdf_bytes: bytes) -> list:
        """
        Renders each page of the PDF to a PNG image at 150 DPI.
        Uploads each image to MinIO.
        Returns a list of dicts with page metadata.
        """
        doc = pymupdf.open("pdf", pdf_bytes)
        results = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)

            img_bytes = pix.tobytes("png")

            object_name = f"{document_id}/page_{page_num + 1}.png"
            minio_path = minio_client.upload_fileobj(
                io.BytesIO(img_bytes),
                object_name,
                bucket=self.bucket
            )
            results.append({
                "page_number": page_num + 1,
                "minio_path": minio_path,
                "width": pix.width,
                "height": pix.height
            })

        doc.close()
        return results

    # Legacy compat
    def render_document(self, document_id: str, pdf_bytes: bytes) -> list:
        records = self.render_document_with_metadata(document_id, pdf_bytes)
        return [r["minio_path"] for r in records]
