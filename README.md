## Synopsis

This is an Indeed job scraper I created to help look for jobs across the US.  I took inspiration and some code from [here](https://medium.com/@msalmon00/web-scraping-job-postings-from-indeed-96bd588dcb4b) and [here](https://beckernick.github.io/job-discovery/).  This code has a bit more error handling, updates a Google Spreadsheet, and emails a summary message using Gmail. 

## Code Example
Run code with: 

```
python scraper.py
```


## Motivation

This scraper was created so that I could automate the job hunting process by doing multiple searches and filtering out the retrieved jobs.  The code examples I mentioned above did not have good enough error handling to search many states or titles, nor did they create the output I desired. 

## Installation

In order to work on another machine you would need a client_secret.json file that works for both Gmail and a Google sheets. The `pygsheets` docs have a pretty good walkthrough [here](http://pygsheets.readthedocs.io/en/latest/authorizing.html#oauth-credentials) , along with a separate file called private.py in the same directory.  The `private.py`file contains a dictionary of email.
```
email = {
	    'you' : 'you@email.com',
	    'me'  : 'me@email.com',
		}
```


## License

MIT License

Copyright (c) \[2017\] \[Jeremy LaBarge\]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.