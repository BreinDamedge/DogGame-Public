from abc import ABC, abstractmethod
import random
import math

# from document_metadata import DocumentMetadata
from parsing import stemmed_keywords, preprocess_n_stem, word_counts, PPS
from metadata_crud import DocumentMetadataAPI

# natural language tool kit
from nltk.metrics.distance import edit_distance
from indexing import InvertedIndexBase


class RankerBase(ABC):
    @abstractmethod
    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        """returns list of tuples(score, doc_id)"""
        ...


class DummyRanker(RankerBase):
    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        """do nothing"""
        return []


class TitleEditDistanceRanker(RankerBase):
    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        if len(doc_ids_) == 0:
            return []

        score_id_tuples = []

        for id_ in doc_ids_:
            doc_MD: dict = metadatastore_.get(id_)
            doc_title = doc_MD["title"]

            # get the distance (difference) between the query and the title
            score_id_tuples.append(
                (edit_distance(doc_title.lower(), query_.lower()), id_)
            )

        print(score_id_tuples)
        print(len(doc_ids_))
        print(len(score_id_tuples))

        return sorted(score_id_tuples, key=lambda x: x[0])


class TitleHasKeyword(RankerBase):
    """rank results off of how many keywords are in the title of the page"""

    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        # do nothing if there's no documents
        if len(doc_ids_) == 0:
            return []

        # create a container to store scores and ids so that they can be sorted
        score_id_tuples: list[tuple[int, str]] = []
        query_keywords: set[str] = stemmed_keywords(query_)

        # score documents
        for doc_id in doc_ids_:
            # load document metadata from disk
            doc_md: dict = metadatastore_.get(doc_id)

            # calculate score (number of keywords present in query also present in doc title)
            score = len(
                set.intersection(query_keywords, stemmed_keywords(doc_md["title"]))
            )

            # add score to the container
            score_id_tuples.append((score, doc_id))

        print(score_id_tuples)
        print(len(doc_ids_))
        print(len(score_id_tuples))

        # rank the scores
        return sorted(score_id_tuples, key=lambda x: x[0], reverse=True)


class TitleRanker2(RankerBase):
    """rank results checking for key words using edit distance on each word"""

    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        # check if there is a document
        if len(doc_ids_) == 0:
            return []

        # container for the scores and the ids
        score_id_tuples: list[tuple[int, str]] = []

        # query keywods stemmed for comparison to documnet titles
        query_keywords: set[str] = stemmed_keywords(query_)

        # main loop through all documents returned from index
        for docID in doc_ids_:
            # get meta data and title
            doc_MD = metadatastore_.get(docID)
            doc_title = doc_MD["title"]

            # create set of words in the title to use for comparison
            doc_title_words: set[str] = stemmed_keywords(doc_title)

            final_score = 0

            # loop through all words in query
            for keyword in query_keywords:
                if len(keyword) == 0:
                    continue

                closet_match_score = 100

                # loop through all words in title and find the closet match
                for word in doc_title_words:
                    if len(word) == 0:
                        continue

                    # get the edit distance score
                    score = edit_distance(keyword.lower(), word.lower())

                    if score < closet_match_score:
                        closet_match_score = score

                        print(keyword, " -> ", word)

                # normalize and add closet match value to the final score
                if closet_match_score > len(keyword):
                    closet_match_score = 0
                else:
                    closet_match_score = (closet_match_score / len(keyword)) - 1

                    if closet_match_score < 0:
                        closet_match_score *= -1

                final_score += closet_match_score
                print("closet score : ", closet_match_score)

            # normalize and append with current document ID
            final_score /= len(query_keywords)
            print(final_score)

            score_id_tuples.append((final_score, docID))

        # rank the scores
        return sorted(score_id_tuples, key=lambda x: x[0], reverse=True)


class TitleRanker(RankerBase):
    """rank results based off the TitleHasKeyword and TitleEditDistanceRanker search, using weightings"""

    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        # check if there is a document
        if len(doc_ids_) == 0:
            return []

        # set the weight of the title rankers and a total weighting
        # hasKeyword_weight = 8
        # editDist_weight = 2
        # total_weight = hasKeyword_weight + editDist_weight

        # container for the scores and the ids
        score_id_tuples: list[tuple[int, str]] = []

        # container for two title ranker scores
        hasKey_editDist_tuple: list[list[int]] = []

        # query keywods stemmed for comparison to documnet titles
        query_keywords: set[str] = stemmed_keywords(query_)

        # varibles for handling normalizing the scores
        words_in_query = len(query_keywords)
        max_editDist_score = 0

        # score the documents
        for docID in doc_ids_:
            # load documnet metadata from disk
            doc_MD: dict = metadatastore_.get(docID)

            # get document title
            doc_title = doc_MD["title"]

            # getting the different scores
            hasKey_score = len(
                set.intersection(query_keywords, stemmed_keywords(doc_title))
            )
            editDist_score = edit_distance(doc_title.lower(), query_.lower())

            # keep track of max edit distanace value
            if editDist_score > max_editDist_score:
                max_editDist_score = editDist_score
                # print("New max : ", max_editDist_score)

            # normalize hasKey_scores and set weight value if value is not 0
            if hasKey_score > 0:
                # print("Has Key before and after : ")
                # print(hasKey_score)
                # hasKey_score *= hasKeyword_weight / (words_in_query * total_weight)
                hasKey_score /= words_in_query
                # print(hasKey_score)

            # add scores to container
            hasKey_editDist_tuple.append([hasKey_score, editDist_score])

        for score, doc_id in zip(hasKey_editDist_tuple, doc_ids_):
            # normalize editDist_scores and set weight value
            # print("Edit Distance before and after : ")
            # print(score[1])
            score[1] = (score[1] / max_editDist_score) - 1

            # check if score is not 0 (fix bug of score being -0)
            if score[1] < 0:
                score[1] *= -1

            # print(score[1])
            # score[1] /= max_editDist_score
            # score[1] -= 1
            # score[1] *= (-1)

            # if the hasKey_score is 0, then use the total weighting for the edit distance weighting
            # if score[0] > 0:
            #    score[1] *= editDist_weight / total_weight
            score[0] /= 2
            score[1] /= 2

            # print("--------------------------------")
            # print("haskey        =   ", score[0])
            # print("edit distance =   ", score[1])

            # add scores together and append to scores and id container
            final_score = score[0] + score[1]  # / 2
            # print("________________________")
            # print("Final score   =   ", final_score)
            # print("________________________")
            score_id_tuples.append((final_score, doc_id))

        # print(score_id_tuples)
        # print(len(doc_ids_))
        # print(len(score_id_tuples))

        # return sorted and ranked ids with scores
        return sorted(score_id_tuples, key=lambda x: x[0], reverse=True)

    # MAY NEED TO STEM QUERY AND TITLE BEFORE PASSING INTO THIS FUNCTION
    def HasKeyWords(title: set[str], query: set[str]):
        if len(title) == 0 or len(query) == 0:
            return 0

        # loop through and check if there are any similar words
        title_score = 0
        # minimum score word has to reach to be considered similar
        editDist_limit = 0.8

        # loop through words in query
        for keyWord in query:
            if len(keyWord) == 0:
                continue

            keyWord_score = 100

            # loop through words in current title
            for word in title:
                if len(word) == 0:
                    continue

                # get the edit distance score
                score = edit_distance(keyWord.lower(), word.lower())

                # take closet matching word
                if score < keyWord_score:
                    keyWord_score = score

            # check that score is valid and above the limit
            if keyWord_score > (len(keyWord) * (1 - editDist_limit)):
                keyWord_score = 0
            else:
                # normalize
                keyWord_score = ((keyWord_score / len(keyWord)) - 1) * -1

                # if keyWord_score < 0:
                #     keyWord_score *= -1

            title_score += keyWord_score

        title_score /= len(query)

        return title_score


from nltk.stem import PorterStemmer
from parsing import stemmed_keywords


class DocumentTFIDF(RankerBase):
    """helper function which scores the documents against a given word"""

    def caculateTFIDF(
        doc_md_: dict,
        preprocessed_query_: list[str],
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> None:

        try:
            # try to get cached word counts
            doc_word_counts: dict[str, int] = doc_md_["stemmed-term-counts"]
        except KeyError:
            # preprocess and count words and store back to record
            content = preprocess_n_stem(doc_md_["text"], PPS)
            doc_word_counts: dict[str, int] = word_counts(content)
            doc_md_["stemmed-term-counts"] = doc_word_counts
            metadatastore_.update(doc_md_["file_id"], doc_md_)

        # adding up the count of each word in the document that is in the query
        # total_count = 0
        # for query_word in query_:
        #     count = word_count.get(query_word, 0)
        #     total_count += count

        # i need to run through each word in the query and caculate the tf and the number
        # get the count of the total relevant documents or documents containing "query_"
        total_tfidf_score = 0
        total_words_in_doc: int = sum(
            [doc_word_counts[k] for k in doc_word_counts.keys()]
        )
        corpus_size: int = len(indexes_[0].get_ids())  # num_documents in the corpus

        for query_word in preprocessed_query_:
            relevant_docs = indexes_[0].get_relevant_ids(query_word)
            relevant_doc_count = len(relevant_docs)
            if relevant_doc_count == 0:
                continue
            else:
                count = doc_word_counts.get(query_word, 0)
                tf = count / total_words_in_doc
                df = relevant_doc_count
                idf = math.log(
                    (1 + corpus_size) / (1 + df)
                )  # 1s added to avoid division by 0
                total_tfidf_score += tf * idf

        return total_tfidf_score

    """rank results by the tf idf"""

    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        # do nothing if there's no documents
        if len(doc_ids_) == 0:
            return []

        # create a container to store scores and ids so that they can be sorted
        score_id_tuples: list[tuple[int, str]] = []

        # lower and split the query to be a list to be usable
        cleaned_query_words = preprocess_n_stem(query_, PPS).split(" ")

        # score documents
        for doc_id in doc_ids_:
            # load document metadata from disk
            doc_md: dict = metadatastore_.get(doc_id)

            # calculate total tf-idf score
            score = DocumentTFIDF.caculateTFIDF(
                doc_md, cleaned_query_words, metadatastore_, indexes_
            )

            # add score to the container
            score_id_tuples.append((score, doc_id))

        # rank the scores
        return sorted(score_id_tuples, key=lambda x: x[0], reverse=True)


class ShuffleRanker(RankerBase):
    def rank(
        self,
        doc_ids_: set[str],
        query_: str,
        metadatastore_: DocumentMetadataAPI,
        indexes_: list[InvertedIndexBase],
    ) -> list[tuple[float, str]]:
        """whatever"""
        score_id_tuples = [(0, id_) for id_ in doc_ids_]
        random.shuffle(score_id_tuples)
        return score_id_tuples
