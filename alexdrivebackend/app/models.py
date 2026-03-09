from pydantic import BaseModel


class CarMaker(BaseModel):
    MakerNo: int
    MakerName: str


class CarModel(BaseModel):
    ModelNo: int
    ModelName: str
    MakerNo: int


class CarModelDetail(BaseModel):
    ModelDetailNo: int
    ModelDetailName: str
    ModelNo: int


class CarGrade(BaseModel):
    GradeNo: int
    GradeName: str
    ModelDetailNo: int


class CarGradeDetail(BaseModel):
    GradeDetailNo: int
    GradeDetailName: str
    GradeNo: int


class CarColor(BaseModel):
    CKeyNo: int
    ColorName: str


class CarFuel(BaseModel):
    FKeyNo: int
    FuelName: str


class CarMission(BaseModel):
    MKeyNo: int
    MissionName: str


class Danji(BaseModel):
    DanjiNo: int
    DanjiName: str


class FilterData(BaseModel):
    makers: list[CarMaker]
    models: dict[str, list[CarModel]]
    modelDetails: dict[str, list[CarModelDetail]]
    grades: dict[str, list[CarGrade]]
    gradeDetails: dict[str, list[CarGradeDetail]]
    colors: list[CarColor]
    fuels: list[CarFuel]
    missions: list[CarMission]
    danjis: list[Danji]


class CarListing(BaseModel):
    encryptedId: str
    imageUrl: str
    name: str
    year: str
    mileage: str
    fuel: str
    transmission: str
    price: str
    location: str
    dealer: str
    phone: str
    blurDataUrl: str = ""


class OptionGroup(BaseModel):
    group: str
    items: list[str]


class CarDetail(BaseModel):
    encryptedId: str
    name: str
    images: list[str]
    year: str
    mileage: str
    fuel: str
    transmission: str
    price: str
    color: str
    engineCapacity: str
    carNumber: str
    location: str
    options: list[OptionGroup]
    dealer: str
    phone: str
    registrationDate: str
    modelYear: str


class CarListingsResponse(BaseModel):
    listings: list[CarListing]
    total: int
