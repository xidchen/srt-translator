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


def google_translate(target_lang: str, text: str) -> str:
    url = cfg.google_translate
    params = {"sl": "zh-CN", "hl": target_lang, "q": f"{text}"}
    proxies = {"https": cfg.proxy_address}
    timeout = cfg.remote_api_timeout
    try:
        response = requests.get(url, params, timeout=timeout, proxies=proxies)
    except TimeoutError:
        time.sleep(cfg.time_to_sleep)
        response = requests.get(url, params, timeout=timeout, proxies=proxies)
    time.sleep(cfg.time_to_sleep)
    if response.status_code == 200:
        pattern = '<div class="result-container">(.*?)</div>'
        raw_result = re.findall(pattern, response.text, re.S)[0]
        result = raw_result.replace("&#39;", "'").replace("&quot;", '"')
        return result
    else:
        print(f"Google Translate failed {response.status_code}")
        return cfg.translate_error


def translate_srt_files(output_lang: list[str]) -> None:
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
                        lines = utils.remove_consecutive_newlines(lines)
                        texts = [line for i, line in enumerate(lines) if i % 4 == 2]
                        text_in_input_lang = utils.drop_unnecessary_whitespace(
                            ''.join(texts)
                        )
                        texts_in_output_lang = []
                        for target_lang in output_lang:
                            text_in_target_lang = google_translate(
                                target_lang=target_lang, text=text_in_input_lang
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
    translate_srt_files(cfg.output_lang)
