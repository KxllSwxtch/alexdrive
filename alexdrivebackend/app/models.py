from pydantic import BaseModel


class CarMaker(BaseModel):
    bm_no: str
    bm_name: str
    bm_logoImage: str = ""


class CarModel(BaseModel):
    bo_no: str
    bo_name: str
    bo_faceImage: str = ""
    bo_startDate: str = ""
    bo_endDate: str = ""
    bo_group: str = ""


class CarSeries(BaseModel):
    bs_no: str
    bs_name: str
    bd: list[dict] = []  # [{bd_no, bd_name}]


class CarColor(BaseModel):
    bc_no: str
    bc_name: str
    bc_rgb1: str = ""
    bc_rgb2: str = ""


class FilterData(BaseModel):
    makers: list[CarMaker]
    colors: list[CarColor]
    fuels: list[dict]
    transmissions: list[dict]


class CarListing(BaseModel):
    encryptedId: str
    imageUrl: str
    name: str
    year: str
    mileage: str
    fuel: str
    transmission: str
    price: str
    priceMl: int = 0  # price in man-won (만원)
    dealer: str = ""
    phone: str = ""


class OptionGroup(BaseModel):
    group: str
    items: list[str]


class InspectionData(BaseModel):
    vin: str = ""
    mileage: str = ""
    emissions: str = ""
    has_accident: bool | None = None
    has_simple_repair: bool | None = None
    inspector_notes: str = ""
    inspection_date: str = ""
    photos: list[str] = []
    stamp_url: str = ""


class CarDetail(BaseModel):
    encryptedId: str
    name: str
    images: list[str]
    year: str
    mileage: str
    fuel: str
    transmission: str
    price: str
    priceMl: int = 0
    color: str = ""
    carNumber: str = ""
    options: list[OptionGroup] = []
    dealer: str = ""
    phone: str = ""
    description: str = ""
    info: dict = {}
    pricing: dict = {}
    specs: dict = {}
    inspection: dict = {}


class CarListingsResponse(BaseModel):
    listings: list[CarListing]
    total: int
    hasNext: bool = False
