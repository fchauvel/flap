#
# This file is part of Flap.
#
# Flap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Flap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flap.  If not, see <http://www.gnu.org/licenses/>.
#


from flap.substitutions.commons import FileWrapper
from flap.substitutions.misc import EndInput
from flap.substitutions.comments import CommentsRemover
from flap.substitutions.files import Input, SubFileExtractor, SubFile, Include, IncludeOnly
from flap.substitutions.graphics import GraphicsPath, IncludeGraphics, Overpic, IncludeSVG, Overpic
from flap.substitutions.bibliography import Bibliography


class ProcessorFactory:
    """
    Create chains of processors
    """

    @staticmethod
    def chain(proxy, source, processors):
        pipeline = source
        for eachProcessor in processors:
            pipeline = eachProcessor(pipeline, proxy)
        return pipeline

    def input_merger(self, file, proxy):
        return ProcessorFactory.chain(
            proxy,
            CommentsRemover(FileWrapper(file)),
            [SubFileExtractor, SubFile, Input, EndInput])

    def flap_pipeline(self, proxy, file):
        return ProcessorFactory.chain(
            proxy,
            self.input_merger(file, proxy),
            [Include, IncludeOnly, GraphicsPath, IncludeGraphics, IncludeSVG, Overpic, Bibliography])