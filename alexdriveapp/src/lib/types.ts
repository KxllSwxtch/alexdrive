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

export interface CarOption {
  CarOptionNo: number;
  CarOptionName: string;
  CarOptionGroupName: string;
}

export interface Danji {
  DanjiNo: number;
  DanjiName: string;
}

export interface FilterData {
  makers: CarMaker[];
  models: Record<number, CarModel[]>;
  modelDetails: Record<number, CarModelDetail[]>;
  grades: Record<number, CarGrade[]>;
  gradeDetails: Record<number, CarGradeDetail[]>;
  colors: CarColor[];
  fuels: CarFuel[];
  missions: CarMission[];
  danjis: Danji[];
}

export interface CarListingParams {
  CarSiDoNo?: string;
  CarSiDoAreaNo?: string;
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
  CarInsurance?: string;
  CarPhoto?: string;
  CarSalePrice?: string;
  CarInspection?: string;
  CarLease?: string;
  SearchName?: string;
  SearchCarNo?: string;
  PageNow?: number;
  PageSize?: number;
  PageSort?: string;
  PageAscDesc?: string;
}

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
  inspectionUrl: string | null;
  blurDataUrl?: string;
}
