// Filter hierarchy (5 levels)
export interface CarMaker {
  MakerNo: number;
  MakerName: string;
}

export interface CarModel {
  ModelNo: number;
  ModelName: string;
  MakerNo: number;
}

export interface CarModelDetail {
  ModelDetailNo: number;
  ModelDetailName: string;
  ModelNo: number;
}

export interface CarGrade {
  GradeNo: number;
  GradeName: string;
  ModelDetailNo: number;
}

export interface CarGradeDetail {
  GradeDetailNo: number;
  GradeDetailName: string;
  GradeNo: number;
}

// Filter options
export interface CarColor {
  CKeyNo: number;
  ColorName: string;
}

export interface CarFuel {
  FKeyNo: number;
  FuelName: string;
}

export interface CarMission {
  MKeyNo: number;
  MissionName: string;
}

export interface Danji {
  DanjiNo: number;
  DanjiName: string;
}

// Filter data (all loaded upfront)
export interface FilterData {
  makers: CarMaker[];
  models: Record<string, CarModel[]>;
  modelDetails: Record<string, CarModelDetail[]>;
  grades: Record<string, CarGrade[]>;
  gradeDetails: Record<string, CarGradeDetail[]>;
  colors: CarColor[];
  fuels: CarFuel[];
  missions: CarMission[];
  danjis: Danji[];
}

// Listing params (carmanager query params)
export interface CarListingParams {
  CarMakerNo?: string;
  CarModelNo?: string;
  CarModelDetailNo?: string;
  CarGradeNo?: string;
  CarGradeDetailNo?: string;
  CarYearFrom?: string;
  CarYearTo?: string;
  CarMileageFrom?: string;
  CarMileageTo?: string;
  CarPriceFrom?: string;
  CarPriceTo?: string;
  CarMissionNo?: string;
  CarFuelNo?: string;
  CarColorNo?: string;
  DanjiNo?: string;
  CarLpg?: string;
  CarInspection?: string;
  CarPhoto?: string;
  CarSalePrice?: string;
  CarLease?: string;
  SearchName?: string;
  SearchCarNo?: string;
  PageNow?: number;
  PageSize?: number;
  PageSort?: string;
  PageAscDesc?: string;
}

// Listing
export interface CarListing {
  encryptedId: string;
  imageUrl: string;
  name: string;
  year: string;
  mileage: string;
  fuel: string;
  transmission: string;
  price: string;
  location: string;
  dealer: string;
  phone: string;
}

// Detail
export interface CarDetail {
  encryptedId: string;
  name: string;
  images: string[];
  year: string;
  mileage: string;
  fuel: string;
  transmission: string;
  price: string;
  color: string;
  engineCapacity: string;
  carNumber: string;
  location: string;
  options: { group: string; items: string[] }[];
  dealer: string;
  phone: string;
  registrationDate: string;
  modelYear: string;
  inspectionUrl?: string;
  blurDataUrl?: string;
}
