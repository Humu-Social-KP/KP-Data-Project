from dataclasses import dataclass, asdict
from typing import Tuple, List, Union

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup, Tag


# TODO: add logging instead of print methods

class City:
    """Список міст, що використовується в URL для запиту списку репетиторів у форматі:
    https://buki.com.ua/tutors/%City.attribute%

    До прикладу:
    https://buki.com.ua/tutors/Kamyanets-Podilskyy
    """

    kp = "Kamyanets-Podilskyy"
    khm = "khmelnytskyy"
    che = "chernivtsi"


@dataclass
class BukiTeacher:
    name: str
    education: str
    experience: str
    description: str
    rating: float
    reviews: int
    price: int
    page_link: str
    tags: str

    @classmethod
    def parse_element(cls, element: Tag):
        name_element = element.select_one(".name-wrap").a
        education = element.select_one(".education")

        if element.select_one(".reviews-mark"):
            rating = float(element.select_one(".reviews-mark").text)
            reviews = int(element.select_one(".reviews_count button").text.split(": ")[-1])
        else:
            rating = reviews = None

        return BukiTeacher(
            name=name_element.text,
            education=education.span.text if education else None,
            experience=element.select_one(".practices").text.split(": ")[-1],
            description=element.select_one(".description").text,
            rating=rating,
            reviews=reviews,
            price=int(element.select_one(".rate-value").text),
            page_link=name_element["href"],
            tags=",".join(item.text for item in element.select(".tutor_item")),
        )


def scrape_data(city: str = City.kp):
    page_url = f"https://buki.com.ua/tutors/{city}" + "/{}"
    print(f"Start Buki parser for: {city}")

    ua = UserAgent()
    session = requests.Session()
    session.headers.update({"User-Agent": ua.random})

    data = list()
    next_page = 1

    while next_page:
        print(f"Start parsing page: {next_page}")
        items, next_page = scrape_page_data(session=session, url=page_url.format(next_page))
        data.extend(items)

        print(f".. parsing done with {len(items)} results.\n"
              f"First result is {items[0]}\n\n")

    return list(map(asdict, data))


def scrape_page_data(session: requests.Session, url: str) -> Tuple[List[BukiTeacher], Union[int, None]]:
    response = session.get(url)
    items = list()
    next_page = None

    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")

        for user_element in soup.select(".user-item-wrapper"):
            items.append(BukiTeacher.parse_element(user_element))

        pages = soup.select("._pages a")
        active_page = next(filter(lambda page: "active" in page["class"], pages)).text

        if pages[-1].text != active_page:
            next_page = int(active_page) + 1

    return items, next_page


def main():
    # TODO: add ArgumentParser for attributes
    # TODO: add writing to JSON/CSV
    # TODO: add statistics after scrapping using pandas
    items = scrape_data(city=City.che)
    # print(items)


if __name__ == '__main__':
    main()
