import os
import re
import sys
import time

import requests

import cfg
import utils


root_dir = os.getcwd()
input_dir = os.path.join(root_dir, cfg.input_dir)
output_dir = os.path.join(root_dir, cfg.output_dir)

if not os.path.exists(input_dir):
    print(f"Input directory {cfg.input_dir} does not exist.")
    sys.exit(1)
if not os.path.exists(output_dir):
    print(f"Create output directory {output_dir}.")
    os.makedirs(output_dir)


def google_translate(source_lang: str, target_lang: str, text: str) -> str:
    url = cfg.google_translate
    q = text.replace(cfg.single_enter, cfg.pipe_double_enter)
    params = {"sl": source_lang, "hl": target_lang, "q": f"{q}"}
    timeout = cfg.remote_api_timeout
    try:
        response = requests.get(url, params, timeout=timeout)
    except TimeoutError:
        time.sleep(cfg.time_to_sleep)
        response = requests.get(url, params, timeout=timeout)
    time.sleep(cfg.time_to_sleep)
    if response.status_code == 200:
        pattern = '<div class="result-container">(.*?)</div>'
        raw_result = re.findall(pattern, response.text, re.S)[0]
        result = raw_result.replace("&#39;", "'").replace("&quot;", '"')
        result = result.replace(cfg.pipe_double_enter, cfg.single_enter)
        result = result.replace(cfg.double_enter, cfg.single_enter)
        final_result = result.strip()
        return final_result
    else:
        print(f"Google Translate failed {response.status_code}")
        return cfg.translate_error


def translate_srt_files(input_lang: str, output_lang: list[str]) -> None:
    for dirpath, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.endswith(cfg.input_srt_suffix):
                input_file_path = os.path.join(dirpath, filename)
                output_file_path = input_file_path.replace(
                    cfg.input_dir, cfg.output_dir
                ).replace(cfg.input_srt_suffix, cfg.output_srt_suffix)
                output_dir_path = os.path.dirname(output_file_path)
                if not os.path.exists(output_dir_path):
                    os.makedirs(output_dir_path)
                with open(input_file_path, 'r', encoding='utf-8') as f_in:
                    with open(output_file_path, 'w', encoding='utf-8') as f_out:
                        lines = f_in.readlines()
                        lines = utils.remove_blank_subscript(lines)
                        texts = [line for i, line in enumerate(lines) if i % 4 == 2]
                        text_in_input_lang = utils.drop_unnecessary_whitespace(
                            ''.join(texts)
                        )
                        texts_in_output_lang = []
                        source_lang = input_lang
                        for target_lang in output_lang:
                            text_in_target_lang = google_translate(
                                source_lang=source_lang,
                                target_lang=target_lang,
                                text=text_in_input_lang
                            )
                            if text_in_target_lang == cfg.translate_error:
                                sys.exit(1)
                            texts_in_target_lang = text_in_target_lang.split('\n')
                            texts_in_target_lang = [
                                t[0].upper() + t[1:] for t in texts_in_target_lang
                            ]
                            texts_in_output_lang.append(texts_in_target_lang)
                        for i, line in enumerate(lines):
                            if i % 4 in {0, 1}:
                                f_out.write(line)
                            elif i % 4 == 2:
                                for texts_in_target_lang in texts_in_output_lang:
                                    f_out.write(texts_in_target_lang[i // 4])
                                    f_out.write('\n')
                            elif i % 4 == 3:
                                f_out.write('\n')
                input_file_path = utils.last_two_levels(input_file_path)
                output_file_path = utils.last_two_levels(output_file_path)
                print(f"{input_file_path} -> {output_file_path}")


if __name__ == "__main__":
    translate_srt_files(cfg.input_lang, cfg.output_lang)
