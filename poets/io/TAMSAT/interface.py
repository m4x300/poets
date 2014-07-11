# Copyright (c) 2014, Vienna University of Technology (TU Wien), Department
# of Geodesy and Geoinformation (GEO).
# All rights reserved.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL VIENNA UNIVERSITY OF TECHNOLOGY,
# DEPARTMENT OF GEODESY AND GEOINFORMATION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author: Thomas Mistelbauer Thomas.Mistelbauer@geo.tuwien.ac.at
# Creation date: 2014-06-13

import datetime
import pandas as pd
import requests
import os
from poets.settings import Settings
from poets.io.source_base import BasicSource


class TAMSAT(BasicSource):
    """
    Source Class for TAMSAT data.
    http://www.met.reading.ac.uk/~tamsat/

    Attributes
    ----------
    name : str
        Name of the data source
    source_path : str
        Link to data source
    filename : str
        Structure/convention of the file name
    dirstruct : list of strings
        Structure of source directory
        Each list item represents a subdirectory
    begin_date : datetime.date
        Date, from which on data is available
    variables : list of strings
        Variables used from data source
    """

    def __init__(self, **kwargs):

        name = 'TAMSAT'
        source_path = "http://www.met.reading.ac.uk/~tamsat/public_data"
        dirstruct = ['YYYY', 'MM']
        filename = "rfe{YYYY}_{MM}-dk{P}.nc"

        begin_date = datetime.date(1983, 01, 01)
        variables = ['rfe']

        if source_path[-1] != '/':
            source_path += '/'

        super(TAMSAT, self).__init__(name, source_path, filename, dirstruct,
                                     begin_date, variables)

    def download(self, download_path=None, begin=None, end=None):
        """
        Download latest TAMSAT RFE dekadal data

        Parameters
        ----------
        download_path : str
            Path where to save the downloaded files.
        begin : datetime.date
            Optional, set either to first date of remote repository or date of
            last file in local repository
        end : datetime.date
            Optional, set to today if none given
        """

        if begin == None:
            dates = self._check_current_date(begin=False)
            if dates is not None:
                begin = datetime.datetime.now()
                for region in Settings.regions:
                    for var in self.variables:
                        if dates[region][var][1] is not None:
                            if dates[region][var][1] < begin:
                                begin = dates[region][var][1]
                        else:
                            begin = self.begin_date
            else:
                begin = self.begin_date

        if download_path == None:
            download_path = os.path.join(Settings.tmp_path, self.name)

        if end == None:
            end = datetime.date.today()

        print('[INFO] downloading data from ' + str(begin) + ' - '
              + str(end))

        # create daterange on monthly basis
        mon_from = datetime.date(begin.year, begin.month, 1)
        mon_to = datetime.date(end.year, end.month, 1)
        daterange = pd.date_range(start=mon_from, end=mon_to, freq='MS')

        # loop through daterange
        for i, dat in enumerate(daterange):
            year = str(dat.year)
            month = str("%02d" % (dat.month,))
            path = self.source_path + year + '/' + month + '/'
            fname = self.filename.replace('{YYYY}', year).replace('{MM}',
                                                                  month)

            dekads = range(3)

            # get dekad of first and last interval based on input dates
            if i == 0 and begin.day > 1:
                if begin.day < 11:
                    dekads = [0, 1, 2]
                elif begin.day >= 11 and begin.day < 21:
                    dekads = [1, 2]
                elif begin.day == 21:
                    dekads = [2]
            elif i == (len(daterange) - 1) and end.day < 21:
                if end.day < 11:
                    dekads = [0]
                else:
                    dekads = [0, 1]

            # loop through dekads
            for j in dekads:
                filepath = path + fname.replace('{P}', str(j + 1))
                r = requests.get(filepath)
                if r.status_code == 200:
                    # check if year folder is existing
                    if not os.path.exists(download_path):
                        print('[INFO] output path does not exist...'
                              'creating path')
                        os.makedirs(download_path)

                    # download file
                    newfile = os.path.join(download_path,
                                           filepath.split('/')[-1])
                    if not os.path.exists(newfile):
                        r = requests.get(filepath, stream=True)
                        with open(newfile, 'wb') as f:
                            f.write(r.content)
                            print '[INFO] downloading file ' + filepath
                    else:
                        print('[INFO] file ' + filepath.split('/')[-1] +
                              ' already exists - nothing to download')