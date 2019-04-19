from src.utils import loadConfiguration, getLogger
from src import fbcrawlerutils as fbutil
from src.database import Database
from src.webdriver import WebDriver
from threading import Thread

config = loadConfiguration("config/config.yaml")


class Crawler(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.driver = WebDriver(config['webdriver']['chromeoptions']).getDriver()
        fbutil.login(self.driver)
        self.idle = True

    def run(self):
        while True:
            groupSlug = self.queue.get()
            self.idle = False
            databaseSession = False
            logger = getLogger(groupSlug)
            logger.info("Crawling started.")
            try:
                database = Database(groupSlug)
                databaseSession = True
                self.driver.get(config['input']['url'].format(groupSlug))
                index = 0
                posts = []
                logger.info("Scrolling posts of : " + str(groupSlug))
                while index < config['input']['limit']:
                    try:
                        postElement = fbutil.getPostAtIndex(self.driver, index, logger)
                        bodyOfPost = fbutil.getBodyOfPost(postElement, logger)
                        timestamp = fbutil.getEpochOfPost(postElement, index, logger)
                        linkToPost = fbutil.getLinkToPost(postElement, index, logger)
                        if self.isPostSignificant(bodyOfPost):
                            keywordMatches = self.getKeywordMatches(bodyOfPost)
                            logger.debug("Inserting post number " + str(index) + " to database")
                            post = (linkToPost, timestamp, str(keywordMatches), bodyOfPost.encode("utf-8"))
                            database.insertPost(post)
                    except Exception as e:
                        logger.error("Error in post number : " + str(index))
                        logger.exception(repr(e))
                    index += 1
                logger.info("Completed crawling " + str(groupSlug))
            except Exception as e:
                logger.exception(repr(e))
            finally:
                if databaseSession:
                    database.closeSession()
                self.idle = True
                self.queue.task_done()

    @staticmethod
    def isPostSignificant(bodyOfPost):
        searchSpace = bodyOfPost.lower()
        allKeywords = config['input']['keywords']
        allExceptions = config['input']['exceptions']
        if any(keyword in searchSpace for keyword in allKeywords):
            if not any(exceptionWord in searchSpace for exceptionWord in allExceptions):
                return True
        return False

    @staticmethod
    def getKeywordMatches(bodyOfPost):
        searchSpace = bodyOfPost.lower()
        allKeywords = config['input']['keywords']
        keywordMatches = []
        for keyword in allKeywords:
            if keyword in searchSpace:
                keywordMatches.append(keyword)
        return keywordMatches
