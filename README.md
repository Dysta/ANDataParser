# ANDataParser
An open source repository that scrappe and parse scrutins and law text from french national assembly.

## How to use
Think this repository as an api. \
`BASE_URL=https://raw.githubusercontent.com/Dysta/ANDataParser/refs/heads/main/` \
or to the official french national assembly : \
`BASE_URL=https://www.assemblee-nationale.fr/dyn/17/`

## Data
In the data repository, all scrutins and law texts are in `/data/dyn/17/scrutins.json`. \
Each object have a `url` and `text_url` property. It point either to the scrutin or the law text. \
To the scrutin or the law_text parsed object, add `/data` to the property's value and use the repos url as a base api. \
To the official web page, just use the french NA base url.
