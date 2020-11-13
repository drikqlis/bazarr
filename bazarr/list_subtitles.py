# coding=utf-8

import gc
import os
import logging
import ast
import re
from guess_language import guess_language
from subliminal_patch import core, search_external_subtitles
from subzero.language import Language

from database import database
from get_languages import alpha2_from_alpha3, get_language_set
from config import settings
from helper import path_mappings, get_subtitle_destination_folder

from embedded_subs_reader import embedded_subs_reader
from event_handler import event_stream
from charamel import Detector

gc.enable()

global hi_regex
hi_regex = re.compile(r'[*¶♫♪].{3,}[*¶♫♪]|[\[\(\{].{3,}[\]\)\}](?<!{\\an\d})')


def store_subtitles(original_path, reversed_path):
    logging.debug('BAZARR started subtitles indexing for this file: ' + reversed_path)
    actual_subtitles = []
    if os.path.exists(reversed_path):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(reversed_path)
                for subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        if (settings.general.getboolean("ignore_pgs_subs") and subtitle_codec.lower() == "pgs") or \
                                (settings.general.getboolean("ignore_vobsub_subs") and subtitle_codec.lower() ==
                                 "vobsub"):
                            logging.debug("BAZARR skipping %s sub for language: %s" % (subtitle_codec, alpha2_from_alpha3(subtitle_language)))
                            continue

                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ":forced"
                            if subtitle_hi:
                                lang = lang + ":hi"
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(reversed_path)[1], reversed_path))
                pass

        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        try:
            dest_folder = get_subtitle_destination_folder()
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(reversed_path, languages=get_language_set(),
                                                  only_one=settings.general.getboolean('single_language'))
            full_dest_folder_path = os.path.dirname(reversed_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(reversed_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.items():
                subtitle_path = get_external_subtitles_path(reversed_path, subtitle)
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append(
                        [str("pb"), path_mappings.path_replace_reverse(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)):
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append(
                        [str("pb:forced"), path_mappings.path_replace_reverse(subtitle_path)])
                elif not language:
                    continue
                elif str(language) != 'und':
                    if language.forced:
                        language_str = str(language)
                    elif language.hi:
                        language_str = str(language) + ':hi'
                    else:
                        language_str = str(language)
                    logging.debug("BAZARR external subtitles detected: " + language_str)
                    actual_subtitles.append([language_str, path_mappings.path_replace_reverse(subtitle_path)])

        database.execute("UPDATE table_episodes SET subtitles=? WHERE path=?",
                         (str(actual_subtitles), original_path))
        matching_episodes = database.execute("SELECT sonarrEpisodeId, sonarrSeriesId FROM table_episodes WHERE path=?",
                                   (original_path,))

        for episode in matching_episodes:
            if episode:
                logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
                list_missing_subtitles(epno=episode['sonarrEpisodeId'])
            else:
                logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + reversed_path)

    return actual_subtitles


def store_subtitles_movie(original_path, reversed_path):
    logging.debug('BAZARR started subtitles indexing for this file: ' + reversed_path)
    actual_subtitles = []
    if os.path.exists(reversed_path):
        if settings.general.getboolean('use_embedded_subs'):
            logging.debug("BAZARR is trying to index embedded subtitles.")
            try:
                subtitle_languages = embedded_subs_reader.list_languages(reversed_path)
                for subtitle_language, subtitle_forced, subtitle_hi, subtitle_codec in subtitle_languages:
                    try:
                        if (settings.general.getboolean("ignore_pgs_subs") and subtitle_codec.lower() == "pgs") or \
                                (settings.general.getboolean("ignore_vobsub_subs") and subtitle_codec.lower() ==
                                 "vobsub"):
                            logging.debug("BAZARR skipping %s sub for language: %s" % (subtitle_codec, alpha2_from_alpha3(subtitle_language)))
                            continue

                        if alpha2_from_alpha3(subtitle_language) is not None:
                            lang = str(alpha2_from_alpha3(subtitle_language))
                            if subtitle_forced:
                                lang = lang + ':forced'
                            if subtitle_hi:
                                lang = lang + ':hi'
                            logging.debug("BAZARR embedded subtitles detected: " + lang)
                            actual_subtitles.append([lang, None])
                    except:
                        logging.debug("BAZARR unable to index this unrecognized language: " + subtitle_language)
                        pass
            except Exception as e:
                logging.exception(
                    "BAZARR error when trying to analyze this %s file: %s" % (os.path.splitext(reversed_path)[1], reversed_path))
                pass

        brazilian_portuguese = [".pt-br", ".pob", "pb"]
        brazilian_portuguese_forced = [".pt-br.forced", ".pob.forced", "pb.forced"]
        try:
            dest_folder = get_subtitle_destination_folder() or ''
            core.CUSTOM_PATHS = [dest_folder] if dest_folder else []
            subtitles = search_external_subtitles(reversed_path, languages=get_language_set())
            full_dest_folder_path = os.path.dirname(reversed_path)
            if dest_folder:
                if settings.general.subfolder == "absolute":
                    full_dest_folder_path = dest_folder
                elif settings.general.subfolder == "relative":
                    full_dest_folder_path = os.path.join(os.path.dirname(reversed_path), dest_folder)
            subtitles = guess_external_subtitles(full_dest_folder_path, subtitles)
        except Exception as e:
            logging.exception("BAZARR unable to index external subtitles.")
            pass
        else:
            for subtitle, language in subtitles.items():
                subtitle_path = get_external_subtitles_path(reversed_path, subtitle)
                if str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese)):
                    logging.debug("BAZARR external subtitles detected: " + "pb")
                    actual_subtitles.append([str("pb"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif str(os.path.splitext(subtitle)[0]).lower().endswith(tuple(brazilian_portuguese_forced)):
                    logging.debug("BAZARR external subtitles detected: " + "pb:forced")
                    actual_subtitles.append([str("pb:forced"), path_mappings.path_replace_reverse_movie(subtitle_path)])
                elif not language:
                    continue
                elif str(language.basename) != 'und':
                    if language.forced:
                        language_str = str(language)
                    elif language.hi:
                        language_str = str(language) + ':hi'
                    else:
                        language_str = str(language)
                    logging.debug("BAZARR external subtitles detected: " + language_str)
                    actual_subtitles.append([language_str, path_mappings.path_replace_reverse_movie(subtitle_path)])
        
        database.execute("UPDATE table_movies SET subtitles=? WHERE path=?",
                         (str(actual_subtitles), original_path))
        matching_movies = database.execute("SELECT radarrId FROM table_movies WHERE path=?", (original_path,))

        for movie in matching_movies:
            if movie:
                logging.debug("BAZARR storing those languages to DB: " + str(actual_subtitles))
                list_missing_subtitles_movies(no=movie['radarrId'])
            else:
                logging.debug("BAZARR haven't been able to update existing subtitles to DB : " + str(actual_subtitles))
    else:
        logging.debug("BAZARR this file doesn't seems to exist or isn't accessible.")
    
    logging.debug('BAZARR ended subtitles indexing for this file: ' + reversed_path)

    return actual_subtitles


def list_missing_subtitles(no=None, epno=None, send_event=True):
    if no is not None:
        episodes_subtitles_clause = " WHERE table_episodes.sonarrSeriesId=" + str(no)
    elif epno is not None:
        episodes_subtitles_clause = " WHERE table_episodes.sonarrEpisodeId=" + str(epno)
    else:
        episodes_subtitles_clause = ""
    episodes_subtitles = database.execute("SELECT table_shows.sonarrSeriesId, table_episodes.sonarrEpisodeId, "
                                          "table_episodes.subtitles, table_shows.languages, table_shows.forced, "
                                          "table_shows.hearing_impaired FROM table_episodes LEFT JOIN table_shows "
                                          "on table_episodes.sonarrSeriesId = table_shows.sonarrSeriesId" +
                                          episodes_subtitles_clause)
    if isinstance(episodes_subtitles, str):
        logging.error("BAZARR list missing subtitles query to DB returned this instead of rows: " + episodes_subtitles)
        return

    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for episode_subtitles in episodes_subtitles:
        actual_subtitles_temp = []
        desired_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if episode_subtitles['subtitles'] is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(episode_subtitles['subtitles'])
            else:
                actual_subtitles_temp = ast.literal_eval(episode_subtitles['subtitles'])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if episode_subtitles['languages'] is not None:
            desired_subtitles = ast.literal_eval(episode_subtitles['languages'])
            if desired_subtitles:
                desired_subtitles_enum = enumerate(desired_subtitles)
            else:
                desired_subtitles_enum = None

            if episode_subtitles['hearing_impaired'] == "True" and desired_subtitles is not None:
                for i, desired_subtitle in desired_subtitles_enum:
                    desired_subtitles[i] = desired_subtitle + ":hi"
            elif episode_subtitles['forced'] == "True" and desired_subtitles is not None:
                for i, desired_subtitle in desired_subtitles_enum:
                    desired_subtitles[i] = desired_subtitle + ":forced"
            elif episode_subtitles['forced'] == "Both" and desired_subtitles is not None:
                for desired_subtitle in desired_subtitles:
                    desired_subtitles_temp.append(desired_subtitle)
                    desired_subtitles_temp.append(desired_subtitle + ":forced")
                desired_subtitles = desired_subtitles_temp
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', episode_subtitles['sonarrEpisodeId'],
                                                   episode_subtitles['sonarrSeriesId']]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                elif item[0] == "pt-BR:forced":
                    actual_subtitles_list.append("pb:forced")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            hi_subs_to_remove = []
            for item in missing_subtitles:
                if item + ':hi' in actual_subtitles_list:
                    hi_subs_to_remove.append(item)
            missing_subtitles = list(set(missing_subtitles) - set(hi_subs_to_remove))
            missing_subtitles_global.append(tuple([str(missing_subtitles), episode_subtitles['sonarrEpisodeId'],
                                                   episode_subtitles['sonarrSeriesId']]))

    for missing_subtitles_item in missing_subtitles_global:
        database.execute("UPDATE table_episodes SET missing_subtitles=? WHERE sonarrEpisodeId=?",
                         (missing_subtitles_item[0], missing_subtitles_item[1]))

        if send_event:
            event_stream(type='episode', action='update', series=missing_subtitles_item[2],
                         episode=missing_subtitles_item[1])
            event_stream(type='badges_series')


def list_missing_subtitles_movies(no=None, send_event=True):
    if no is not None:
        movies_subtitles_clause = " WHERE radarrId=" + str(no)
    else:
        movies_subtitles_clause = ""

    movies_subtitles = database.execute("SELECT radarrId, subtitles, languages, forced, hearing_impaired FROM "
                                        "table_movies" + movies_subtitles_clause)
    if isinstance(movies_subtitles, str):
        logging.error("BAZARR list missing subtitles query to DB returned this instead of rows: " + movies_subtitles)
        return
    
    missing_subtitles_global = []
    use_embedded_subs = settings.general.getboolean('use_embedded_subs')
    for movie_subtitles in movies_subtitles:
        actual_subtitles_temp = []
        desired_subtitles_temp = []
        actual_subtitles = []
        desired_subtitles = []
        missing_subtitles = []
        if movie_subtitles['subtitles'] is not None:
            if use_embedded_subs:
                actual_subtitles = ast.literal_eval(movie_subtitles['subtitles'])
            else:
                actual_subtitles_temp = ast.literal_eval(movie_subtitles['subtitles'])
                for subtitle in actual_subtitles_temp:
                    if subtitle[1] is not None:
                        actual_subtitles.append(subtitle)
        if movie_subtitles['languages'] is not None:
            desired_subtitles = ast.literal_eval(movie_subtitles['languages'])
            if desired_subtitles:
                desired_subtitles_enum = enumerate(desired_subtitles)
            else:
                desired_subtitles_enum = None

            if movie_subtitles['hearing_impaired'] == "True" and desired_subtitles is not None:
                for i, desired_subtitle in desired_subtitles_enum:
                    desired_subtitles[i] = desired_subtitle + ":hi"
            elif movie_subtitles['forced'] == "True" and desired_subtitles is not None:
                for i, desired_subtitle in desired_subtitles_enum:
                    desired_subtitles[i] = desired_subtitle + ":forced"
            elif movie_subtitles['forced'] == "Both" and desired_subtitles is not None:
                for desired_subtitle in desired_subtitles:
                    desired_subtitles_temp.append(desired_subtitle)
                    desired_subtitles_temp.append(desired_subtitle + ":forced")
                desired_subtitles = desired_subtitles_temp
        actual_subtitles_list = []
        if desired_subtitles is None:
            missing_subtitles_global.append(tuple(['[]', movie_subtitles['radarrId']]))
        else:
            for item in actual_subtitles:
                if item[0] == "pt-BR":
                    actual_subtitles_list.append("pb")
                elif item[0] == "pt-BR:forced":
                    actual_subtitles_list.append("pb:forced")
                else:
                    actual_subtitles_list.append(item[0])
            missing_subtitles = list(set(desired_subtitles) - set(actual_subtitles_list))
            hi_subs_to_remove = []
            for item in missing_subtitles:
                if item + ':hi' in actual_subtitles_list:
                    hi_subs_to_remove.append(item)
            missing_subtitles = list(set(missing_subtitles) - set(hi_subs_to_remove))
            missing_subtitles_global.append(tuple([str(missing_subtitles), movie_subtitles['radarrId']]))
    
    for missing_subtitles_item in missing_subtitles_global:
        database.execute("UPDATE table_movies SET missing_subtitles=? WHERE radarrId=?",
                         (missing_subtitles_item[0], missing_subtitles_item[1]))

        if send_event:
            event_stream(type='movie', action='update', movie=missing_subtitles_item[1])
            event_stream(type='badges_movies')


def series_full_scan_subtitles():
    episodes = database.execute("SELECT path FROM table_episodes")
    
    for i, episode in enumerate(episodes, 1):
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))
    
    gc.collect()


def movies_full_scan_subtitles():
    movies = database.execute("SELECT path FROM table_movies")
    
    for i, movie in enumerate(movies, 1):
        store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))
    
    gc.collect()


def series_scan_subtitles(no):
    episodes = database.execute("SELECT path FROM table_episodes WHERE sonarrSeriesId=? ORDER BY sonarrEpisodeId",
                                (no,))
    
    for episode in episodes:
        store_subtitles(episode['path'], path_mappings.path_replace(episode['path']))


def movies_scan_subtitles(no):
    movies = database.execute("SELECT path FROM table_movies WHERE radarrId=? ORDER BY radarrId", (no,))
    
    for movie in movies:
        store_subtitles_movie(movie['path'], path_mappings.path_replace_movie(movie['path']))


def get_external_subtitles_path(file, subtitle):
    fld = os.path.dirname(file)
    
    if settings.general.subfolder == "current":
        path = os.path.join(fld, subtitle)
    elif settings.general.subfolder == "absolute":
        custom_fld = settings.general.subfolder_custom
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    elif settings.general.subfolder == "relative":
        custom_fld = os.path.join(fld, settings.general.subfolder_custom)
        if os.path.exists(os.path.join(fld, subtitle)):
            path = os.path.join(fld, subtitle)
        elif os.path.exists(os.path.join(custom_fld, subtitle)):
            path = os.path.join(custom_fld, subtitle)
        else:
            path = None
    else:
        path = None
    
    return path


def guess_external_subtitles(dest_folder, subtitles):
    for subtitle, language in subtitles.items():
        if not language:
            subtitle_path = os.path.join(dest_folder, subtitle)
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                logging.debug("BAZARR falling back to file content analysis to detect language.")
                detected_language = None

                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > 1*1024*1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                    detected_language = guess_language(text)
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except:
                            logging.debug(
                                "BAZARR skipping this subtitles because we can't decode the file using the "
                                "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue
                    detected_language = guess_language(text)
                except:
                    logging.debug('BAZARR was unable to detect encoding for this subtitles file: %r', subtitle_path)
                finally:
                    if detected_language:
                        logging.debug("BAZARR external subtitles detected and guessed this language: " + str(
                            detected_language))
                        try:
                            subtitles[subtitle] = Language.rebuild(Language.fromietf(detected_language), forced=False,
                                                                   hi=False)
                        except:
                            pass

        # If language is still None (undetected), skip it
        if not language:
            pass

        # Skip HI detection if forced
        elif language.forced:
            pass

        # Detect hearing-impaired external subtitles not identified in filename
        elif not subtitles[subtitle].hi:
            subtitle_path = os.path.join(dest_folder, subtitle)

            # check if file exist:
            if os.path.exists(subtitle_path) and os.path.splitext(subtitle_path)[1] in core.SUBTITLE_EXTENSIONS:
                # to improve performance, skip detection of files larger that 1M
                if os.path.getsize(subtitle_path) > 1 * 1024 * 1024:
                    logging.debug("BAZARR subtitles file is too large to be text based. Skipping this file: " +
                                  subtitle_path)
                    continue

                with open(subtitle_path, 'rb') as f:
                    text = f.read()

                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    detector = Detector()
                    try:
                        guess = detector.detect(text)
                    except:
                        logging.debug("BAZARR skipping this subtitles because we can't guess the encoding. "
                                      "It's probably a binary file: " + subtitle_path)
                        continue
                    else:
                        logging.debug('BAZARR detected encoding %r', guess)
                        try:
                            text = text.decode(guess)
                        except:
                            logging.debug("BAZARR skipping this subtitles because we can't decode the file using the "
                                          "guessed encoding. It's probably a binary file: " + subtitle_path)
                            continue

                if bool(re.search(hi_regex, text)):
                    subtitles[subtitle] = Language.rebuild(subtitles[subtitle], forced=False, hi=True)
    return subtitles
