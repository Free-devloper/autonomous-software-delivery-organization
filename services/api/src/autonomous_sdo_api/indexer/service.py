from autonomous_sdo_api.indexer.models import FileSymbolsResponse
from autonomous_sdo_api.indexer.parsers import detect_language, get_language_parser


class SymbolExtractionService:
    """Extracts semantic code symbols from source files."""

    def extract_symbols(
        self,
        file_path: str,
        content: str,
        commit_sha: str,
    ) -> FileSymbolsResponse:
        """Parse source code content and extract structured code symbols."""
        language = detect_language(file_path)
        parser = get_language_parser(language)

        if parser is None:
            return FileSymbolsResponse(
                commit_sha=commit_sha,
                file_path=file_path,
                language=language,
                symbols=[],
            )

        symbols = parser.parse(content, file_path)
        return FileSymbolsResponse(
            commit_sha=commit_sha,
            file_path=file_path,
            language=language,
            symbols=symbols,
        )
