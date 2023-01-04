# Mail Reply Parser 📧🐍 

[![Python](https://img.shields.io/badge/Made%20with-Python%203.x-blue.svg?style=flat-square&logo=Python&logoColor=white)](https://www.python.org/) 
[![Version](https://img.shields.io/badge/Version-1.0-dc2f02.svg?style=flat-square&logoColor=white)](https://github.com/alfonsrv/mailparser-reply)


### Multi-language email reply parsing for international environments 🌍

Mail clients handle reply formatting differently, making reliable parsing difficult. Thank god we have 
[standards](https://xkcd.com/927/).  This library splits *text-based* emails into separate replies based on common 
headers produced by different, multilingual clients usually indicating separation.

Replies can either present the whole mail message body, or strip headers, signatures and common disclaimers if required. 
Currently supported languages are: English (`en`), German (`de`), French (`fr`) – adding more languages is quite easy.

This is an improved Python implementation of GitHub's Ruby-based [email_reply_parser](https://github.com/github/email_reply_parser/) 
and an adaptation of Zapier's [email-reply-parser](https://github.com/zapier/email-reply-parser) which both split the 
mails in fragments instead of distinct replies. They also only support English.


## ⭐ Features

⭐ Easy to implement  
⭐ Multilanguage Support  
⭐ Text-based mail parsing  
⭐ Detect headers, signatures and disclaimers  
⭐ Easy-to-read code and well-tested  


## Overview 🔭

This library makes it easy to split an incoming mail into replies, making working with emails much more manageable
and easily providing the text content for each reply – with or without signatures, disclaimers and headers.

For example, it can turn the following email:

```
Awesome! I haven't had another problem with it.

Thanks,
alfonsrv

On Wed, Dec 20, 2023 at 13:37, RAUSYS <info@rausys.de> wrote:

> The good news is that I've found a much better query for lastLocation.
> It should run much faster now. Can you double-check?
```

Into just the replied text content:

```
Awesome! I haven't had another problem with it.
```


## Get started 👾

### Installation

```bash
pip install mailparser-reply
```

### Parse Replies

*API docs coming*

---

[![Buy me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/alfonsrv)  
