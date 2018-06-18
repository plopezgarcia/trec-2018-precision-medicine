library(dplyr)

setwd("~/git/plopezgarcia/trec-2018-precision-medicine/eval/2017/official-qrels")

abstracts <- read.table(file = 'qrels-treceval-abstracts.2017.txt', sep = ' ', header = FALSE)

colnames(abstracts) <- c('topic', 'iteration', 'document', 'relevancy')

abstract_annotations <- read.table(file = 'qrels-treceval-abstracts-annotations.2017.txt', sep = ',', header = TRUE)

useful_info <- full_join(abstracts, abstract_annotations, by=c('topic'='trec_topic_number', 'document'='trec_doc_id')) %>%
    select(-iteration) %>% arrange(topic, desc(relevancy))