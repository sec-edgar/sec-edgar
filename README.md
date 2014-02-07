Edgar-Crawler
=============

 Getting filings of various comapanies at once is really a pain but Edgar-Crawler does that for you.
 you can Download all companies  periodic reports, filings and forms from EDGAR database in a single command.
 
 Clone the project or download it as zip. 
 
 Change file.txt to add the name of company's, CIK code and date (prior to) to get the filings of that company.
 
 Now to run it <br/>
   <code> $ python allinone.py </code>
   
 This will download the company's 8-K, 10-K, 10-Q filings of company's listed in file.txt. The data will be saved in "Crawled
 Data" folder in the same folder where allinone.py is.
 
 
 
<h3>The MIT License (MIT) </h3>
<pre>
Copyright (c) <year> <copyright holders>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
</pre>
