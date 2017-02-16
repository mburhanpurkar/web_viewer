from extract_names import app
from extract_names import Parser, Crawler

if __name__ == "__main__":
    master_directories = Crawler()
    app.run()
