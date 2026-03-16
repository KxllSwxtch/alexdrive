from pydantic import BaseModel


class CarMaker(BaseModel):
    MakerNo: str
    MakerName: str


class CarModel(BaseModel):
    ModelNo: str
    ModelName: str
    MakerNo: str


class CarModelDetail(BaseModel):
    ModelDetailNo: str
    ModelDetailName: str
    ModelNo: str


class CarGrade(BaseModel):
    GradeNo: str
    GradeName: str
    ModelDetailNo: str


class CarGradeDetail(BaseModel):
    GradeDetailNo: str
    GradeDetailName: str
    GradeNo: str


class CarColor(BaseModel):
    CKeyNo: str
    ColorName: str


class CarFuel(BaseModel):
    FKeyNo: str
    FuelName: str


class CarMission(BaseModel):
    MKeyNo: str
    MissionName: str


class FilterData(BaseModel):
    makers: list[CarMaker]
    models: dict[str, list[CarModel]]
    modelDetails: dict[str, list[CarModelDetail]]
    grades: dict[str, list[CarGrade]]
    gradeDetails: dict[str, list[CarGradeDetail]]
    colors: list[CarColor]
    fuels: list[CarFuel]
    missions: list[CarMission]
    categories: list[dict]


class CarListing(BaseModel):
    encryptedId: str
    imageUrl: str
    name: str
    year: str
    mileage: str
    fuel: str
    transmission: str
    price: str
    dealer: str
    phone: str


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
    carNumber: str
    options: list[OptionGroup]
    dealer: str
    phone: str
    diagnosticsUrl: str | None = None


class CarListingsResponse(BaseModel):
    listings: list[CarListing]
    total: int
    hasNext: bool = False
