def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()  # must run before any music_processor screen imports

    from music_processor.app import MusicProcessorApp
    MusicProcessorApp().run()


if __name__ == "__main__":
    main()
