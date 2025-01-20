import fire

from .main import update_assistant, prompt

def main():
    fire.Fire({
        "update_assistant": update_assistant,
        "prompt": prompt
    })

if __name__ == '__main__':
    main()