def main() -> None:
    from dotenv import load_dotenv
    from music_processor.app import MusicProcessorApp

    load_dotenv()
    MusicProcessorApp().run()


if __name__ == "__main__":
    main()
