import base64

from openai.types.responses import ResponseInputFileParam
from pydantic import BaseModel


class FilePrompt(BaseModel):
    filename: str
    content_type: str  # e.g. "application/pdf"
    file_data: bytes

    def _encoded(self) -> ResponseInputFileParam:
        base64_string = base64.b64encode(self.file_data).decode("utf-8")
        return {
            "type": "input_file",
            "filename": self.filename,
            "file_data": f"data:{self.content_type};base64,{base64_string}",
        }


class FileURLPrompt(BaseModel):
    """only for remote urls"""

    # filename: str | None = None
    url: str

    def _encoded(self) -> ResponseInputFileParam:
        return {
            "type": "input_file",
            "file_url": self.url,
        }
        # (Filename not allowed for file_url)
        # if self.filename is not None:
        #     result["filename"] = self.filename
        # return result
