let
    Source = Csv.Document(File.Contents(FolderPath & "DimDate.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Date", type date}, {"Month", type text}, {"MonthSort", Int64.Type}, {"Year", Int64.Type}, {"Quarter", Int64.Type}}, "en-US")
in
    Typed
