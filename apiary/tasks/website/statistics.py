"""Pull in statistics for sites."""
# pylint: disable=C0301

from WikiApiary.apiary.tasks import BaseApiaryTask
import logging
import urlparse
import socket


LOGGER = logging.getLogger()

class GetStatisticsTask(BaseApiaryTask):
    """Collect statistics on usage from site."""

    def fetch_statistics(self):
        """Method calls the website API and retrieves site statistics, storing them in the class."""
        if self.has_API():
            return self.fetch_statistics_API()
        elif self.has_StatisticsURL():
            return self.fetch_statistics_statistics()
        else:
            self.log("Website has neither API or Statistics URLs.")
            return False

    def has_StatisticsURL(self):
        """Test if the website has a Statistics URL."""
        if self.statistics_url is not None:
            return True
        else:
            return False

    def fetch_statisitcs_API(self):
        """Get site statistics via the API."""
        stats_url = self.api_url + bot.STATISTICS_API_CALL

    def fetch_statistics_statistics(self):
        """Get the site statistics using the Special:Statistics page."""
        stats_url = self.statistics_url + '&action=raw'

    def run(self, site_id, site, api_url):
        method = "API"
        if method == 'API':
            # Go out and get the statistic information
            data_url = api_url + '?action=query&meta=siteinfo&siprop=statistics&format=json'
            LOGGER.info("Pulling statistics info from %s." % data_url)
            (status, data, duration) = self.pull_json(site, data_url)
        elif method == 'Statistics':
            # Get stats the old fashioned way
            data_url = site['Has statistics URL']
            if "?" in data_url:
                data_url += "&action=raw"
            else:
                data_url += "?action=raw"
            if self.args.verbose >= 2:
                print "Pulling statistics from %s." % data_url

            # This is terrible and should be put into pull_json somewhow
            socket.setdefaulttimeout(15)

            # Get CSV data via raw Statistics call
            req = urllib2.Request(data_url)
            req.add_header('User-Agent', self.config.get('Bumble Bee', 'User-Agent'))
            opener = urllib2.build_opener()

            try:
                t1 = datetime.datetime.now()
                f = opener.open(req)
                duration = (datetime.datetime.now() - t1).total_seconds()
            except Exception, e:
                self.record_error(
                    site=site,
                    log_message="%s" % e,
                    log_type='error',
                    log_severity='normal',
                    log_bot='Bumble Bee',
                    log_url=data_url
                )
                status = False
            else:
                # Create an object that is the same as that returned by the API
                ret_string = f.read()
                ret_string = ret_string.strip()
                if re.match(r'(\w+=\d+)\;?', ret_string):
                    # The return value looks as we expected
                    status = True
                    data = {}
                    data['query'] = {}
                    data['query']['statistics'] = {}
                    items = ret_string.split(";")
                    for item in items:
                        (name, value) = item.split("=")
                        try:
                            # Convert the value to an int, if this fails we skip it
                            value = int(value)
                            if name == "total":
                                name = "pages"
                            if name == "good":
                                name = "articles"
                            if self.args.verbose >= 3:
                                print "Transforming %s to %s" % (name, value)
                            data['query']['statistics'][name] = value
                        except:
                            if self.args.verbose >= 3:
                                print "Illegal value '%s' for %s." % (value, name)
                else:
                    status = False # The result didn't match the pattern expected
                    self.record_error(
                        site=site,
                        log_message="Unexpected response to statistics call",
                        log_type='error',
                        log_severity='normal',
                        log_bot='Bumble Bee',
                        log_url=data_url
                    )
                    LOGGER.info("Result from statistics was not formatted as expected:\n%s" % ret_string)

        ret_value = True
        if status:
            # Record the new data into the DB
            if self.args.verbose >= 2:
                print "JSON: %s" % data
                print "Duration: %s" % duration

            if 'query' in data:
                # Record the data received to the database
                sql_command = """
                    INSERT INTO statistics
                        (website_id, capture_date, response_timer, articles, jobs, users, admins, edits, activeusers, images, pages, views)
                    VALUES
                        (%s, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                data = data['query']['statistics']
                if 'articles' in data:
                    articles = "%s" % data['articles']
                else:
                    articles = 'null'
                if 'jobs' in data:
                    jobs = "%s" % data['jobs']
                else:
                    jobs = 'null'
                if 'users' in data:
                    users = "%s" % data['users']
                else:
                    users = 'null'
                if 'admins' in data:
                    admins = "%s" % data['admins']
                else:
                    admins = 'null'
                if 'edits' in data:
                    edits = "%s" % data['edits']
                else:
                    edits = 'null'
                if 'activeusers' in data:
                    if data['activeusers'] < 0:
                        data['activeusers'] = 0
                    activeusers = "%s" % data['activeusers']
                else:
                    activeusers = 'null'
                if 'images' in data:
                    images = "%s" % data['images']
                else:
                    images = 'null'
                if 'pages' in data:
                    pages = "%s" % data['pages']
                else:
                    pages = 'null'
                if 'views' in data:
                    views = "%s" % data['views']
                else:
                    views = 'null'

                sql_command = sql_command % (
                    site['Has ID'],
                    self.sqlutcnow(),
                    duration,
                    articles,
                    jobs,
                    users,
                    admins,
                    edits,
                    activeusers,
                    images,
                    pages,
                    views)

                self.runSql(sql_command)
                self.stats['statistics'] += 1
            else:
                self.record_error(
                    site=site,
                    log_message='Statistics returned unexpected JSON.',
                    log_type='info',
                    log_severity='normal',
                    log_bot='Bumble Bee',
                    log_url=data_url
                )
                ret_value = False

        else:
            if self.args.verbose >= 3:
                print "Did not receive valid data from %s" % (data_url)
            ret_value = False

        # Update the status table that we did our work!
        self.update_status(site, 'statistics')
        return ret_value



