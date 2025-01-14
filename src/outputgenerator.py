from src.utils import loadConfiguration, getLogger
from src.database import Database
from datetime import datetime
import pathlib

config = loadConfiguration("config/config.yaml")
logger = getLogger("OutputGenerator")

class OutputGenerator:
    def __init__(self, outputFile):
        pathlib.Path(config['output']['directory']).mkdir(parents=True, exist_ok=True)
        self.filename = config['output']['directory']+outputFile

    def generateOuputFromDatabase(self, selectQuery=config['output']['query']):
        for groupSlug in config['input']['groups']:
            try:
                database = Database(groupSlug)
                data = database.select(selectQuery)
                if len(data) > 0:
                    self.appendTableToOutputFile(groupSlug, data)
                database.closeSession()
            except Exception as e:
                logger.exception("Problem in generating output from database for group: "+groupSlug)
        logger.info("Output written to file: "+self.filename)

    def appendTableToOutputFile(self, heading, data):
        f = open(self.filename, "a+", encoding="utf-8")
        f.write(self.getHtmlSourceToWrite(heading, data))
        f.close()

    def getHtmlSourceToWrite(self, heading, data):
        return '''
        <h3>{}</h3>
        <table style="width: 95%; border-collapse: collapse; align:center;" border = "2" cellpadding = "4">
            {}
            {}
        </table>
        <hr>
        '''.format(heading, self.getHtmlTableHeading(), self.getHtmlTableBody(data))

    def getHtmlTableHeading(self):
        columns= ['S. No.', 'Post Time', 'Crawl Time', 'Keywords', 'Body', 'URL']
        heading = "<thead style=\"font-weight:bold;\">";
        for column in columns:
            heading += "<td>{}</td>".format(column)
        heading += "</thead>"
        return heading

    def getHtmlTableBody(self, data):
        index = 1
        body = "<tbody>"
        for row in data:
            body += "<tr>"
            body += "<td>{}</td>".format(index)
            body += "<td>{}</td>".format(datetime.fromtimestamp(row['posttime']).strftime(config['output']['timeformat']))
            body += "<td>{}</td>".format(datetime.fromtimestamp(int(row['timestamp'])).strftime(config['output']['timeformat']))
            body += "<td>{}</td>".format(row['keyword'])
            body += "<td>{}...</td>".format(str(row['body'].decode("utf-8"))[0:config['output']['sizeofbody']])
            body += "<td><a href=\"{}\" target=\"_blank\">Link</a></td>".format(row['link'])
            body += "</tr>"
            index += 1
        body += "</tbody>"
        return body