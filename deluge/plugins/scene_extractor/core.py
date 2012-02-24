#
# core.py
#
# Copyright (C) 2012 Bobby R. Ward <bobbyrward@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
# Copyright (C) 2010 Pedro Algarvio <pedro@algarvio.me>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import logging
import fnmatch
import os
from deluge.plugins_pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from deluge.plugins.scene_extractor.scene_name import SceneName
import rarfile


DEFAULT_PREFS = {
    "subdirs": ['cd1', 'cd2', 'subs'],
    "extract_base": "/media/sf_videos/To Watch/",
}


log = logging.getLogger(__name__)


class Core(CorePluginBase):
    def enable(self):
        self.config = deluge.configmanager.ConfigManager("scene_extractor.conf", DEFAULT_PREFS)

        if 'extract_base' not in self.config['extract_base']:
            self.config["extract_base"] = os.path.join(deluge.configmanager.ConfigManager("core.conf")["download_location"], 'To Watch')

        component.get("EventManager").register_event_handler("TorrentFinishedEvent", self._on_torrent_finished)

    def _on_torrent_finished(self, torrent_id):
        try:
            extract_path = self.find_extract_path(torrent_id)
            rar_files = self.find_rars_to_extract(torrent_id)

            os.makedirs(extract_path)

            for rar in rar_files:
                log.warning('SceneExtractor: Extracting "%s" to "%s"' % (rar, extract_path))
                extractor = rarfile.RarFile(rar)
                extractor.extractall(path=extract_path)
                extractor.close()
        except Exception:
            import traceback
            log.warning("Error in SceneExtractor._on_torrent_finished - " + traceback.format_exc())

    def find_rars_to_extract(self, torrent_id):
        save_path = component.get("TorrentManager")[torrent_id].get_status(["save_path"])["save_path"]
        files = [ f['path'] for f in component.get("TorrentManager")[torrent_id].get_files() ]
        files = fnmatch.filter(files, '*.rar')

        rar_files = []

        if len(files) > 1:
            part01_files = fnmatch.filter(files, '*.part01.rar')

            if part01_files:
                rar_files.extend(os.path.join(save_path, filename) for filename in part01_files)
            else:
                raise Exception('Multiple .rar files found in %s' %root)

        elif files:
            rar_files.extend(os.path.join(save_path, filename) for filename in files)

        return rar_files

    def disable(self):
        component.get("EventManager").deregister_event_handler("TorrentFinishedEvent", self._on_torrent_finished)

    def update(self):
        pass

    def find_extract_path(self, torrent_id):
        name = component.get("TorrentManager")[torrent_id].get_name()
        scene_name = SceneName.parse(name)

        extract_path = []
        extract_path.append(scene_name.release_type)
        extract_path.append(scene_name.name)

        if scene_name.season and scene_name.episode:
            extract_path.append('Season {0}'.format(scene_name.season))
            extract_path.append('Episode {0}'.format(scene_name.episode))
        elif scene_name.episode_date:
            extract_path.append(scene_name.episode_date.strftime('%Y.%m.%d'))

        return os.path.join(self.config['extract_base'], *extract_path)

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config
