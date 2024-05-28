import os

import cfg


replacement_dict = {
    "": "",
}


def process(srt_dir):
    for dir_path, _, file_names in os.walk(srt_dir):
        for file_name in file_names:
            if file_name.endswith(cfg.output_srt_suffix):
                srt_file = os.path.join(dir_path, file_name)
                with open(srt_file, "r", encoding="utf-8") as f:
                    content = f.read()
                for old, new in replacement_dict.items():
                    content = content.replace(old, new)
                with open(srt_file, "w", encoding="utf-8") as f:
                    f.write(content)


if __name__ == "__main__":
    process(cfg.output_dir)
