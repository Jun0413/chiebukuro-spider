# chiebukuro-spider

`scrape.py` is the single Python script to scrape Japanese Question & Answer pairs from [Yahoo! Chiebukuro (知恵袋)](https://chiebukuro.yahoo.co.jp). 

Data retrieved are saved with respect to date. Files are named after `category_year_month`. Files are in JSON format with following attributes:

- *qa_id*: unique id for the question-answer pair, which can be accessed by appending after https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/ [replace with qa_id]

- *qn_title*: title of question. Note this is not complete in common, and needs to be concatenated with qn_desc below to form a complete question.

- *qn_desc*: description of question.

- *best_ans*: best answer. Only one.

- *othr_ans*: list of answers beside best answer.

- *cat*: category. By right this should be "インターネット、通信", but a Q-A can fall under other categories. For example, it can appear as "知恵袋トップ>エンターテインメントと趣味 > ゲーム > 荒野行動 | スマホアプリ" yet still belonging to "インターネット、通信" as "スマホアプリ" is its sub-category. In cases like this, we regard "エンターテインメントと趣味" as its category.

- *subcat*: sub-category. In the example above, "ゲーム" will be the sub-category. It can be empty.

- *subsubcat*: sub-sub-category. In the example above, "荒野行動" will be the sub-sub-category. It can be empty.

To scrape other categories (by default it is "インターネット、通信") from Chiebukuro, set `base_fn` to a name for category, change the `did` part in `base_url` to the id for category. Lastly, under **block for testing**, change `year`, `month`, `day` to the earliest date where no Q-A is available.

To run it (with Python3):
```bash
$ scrapy runspider scrape.py
```
