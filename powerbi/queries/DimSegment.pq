let
    Source = Csv.Document(File.Contents(FolderPath & "DimSegment.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"segment", type text}}, "en-US")
in
    Typed
