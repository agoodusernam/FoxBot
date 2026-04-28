import io
import logging
import typing

import aiohttp
import vt  # type: ignore[import-untyped]
from vt import Object, ClientResponse

logger = logging.getLogger('discord')


class ZipVTClient(vt.Client):
    async def scan_file_async(
            self,
            file: typing.BinaryIO,
            wait_for_completion: bool = False,
            zip_password: str | None = None,
    ) -> Object:
        """Like :func:`scan_file` but returns a coroutine."""
        
        if not isinstance(file, io.IOBase):
            raise TypeError(f"Expected a file to be a file object, got {type(file)}")
        
        logger.debug('Starting upload of file to VT')
        
        # The snippet below could be replaced with this simpler code:
        #
        # form_data = aiohttp.FormData()
        # form_data.add_field('file', file)
        #
        # However, aiohttp.FormData assumes that the server supports RFC 5987 and
        # send a Content-Disposition like:
        #
        # 'form-data; name="file"; filename="foobar"; filename*=UTF-8''foobar
        #
        # AppEngine's upload handler doesn't like the filename*=UTF-8''foobar field
        # and fails with this Content-Disposition header.
        
        part = aiohttp.get_payload(file)
        filename = file.name if hasattr(file, "name") else "unknown"
        disposition = f'form-data; name="file"; filename="{filename}"'
        part.headers["Content-Disposition"] = disposition
        form_data = aiohttp.MultipartWriter("form-data")
        form_data.append_payload(part)
        if zip_password is not None and zip_password.strip() != "":
            form_data.append_form({"password": zip_password.strip()})
        
        upload_url = await self.get_data_async("/files/upload_url")
        logger.debug(f"Upload URL: {upload_url}")
        response = ClientResponse(
                await self._get_session().post(
                        upload_url, data=form_data, proxy=self._proxy,
                ),
        )
        logger.debug(f"Status: {response.status}")
        logger.debug(f"Reason: {response.reason}")
        logger.debug(f"Headers: {response.headers}")
        try:
            logger.debug(f"Raw response: {response.content}")
        except aiohttp.ClientPayloadError:
            logger.debug("Raw response could not be logged.")
        
        analysis = await self._response_to_object(response)
        
        if wait_for_completion:
            logger.debug("Waiting for analysis to complete")
            analysis = await self._wait_for_analysis_completion(analysis)
            logger.debug("Analysis complete")
        
        logger.debug(f"Returned analysis: {analysis.to_dict()}")
        return analysis
