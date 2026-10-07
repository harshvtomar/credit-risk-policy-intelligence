let
    Source = Csv.Document(File.Contents(FolderPath & "FactMonthly.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"month", type text}, {"segment", type text}, {"applications", Int64.Type}, {"defaults", Int64.Type}, {"approved", Int64.Type}, {"approved_defaults", Int64.Type}, {"funded_amount", type number}, {"contribution", type number}, {"month_date", type date}}, "en-US")
in
    Typed
