export interface CarMaker {
  MakerNo: string;
  MakerName: string;
}

export interface CarModel {
  ModelNo: string;
  ModelName: string;
  MakerNo: string;
}

export interface CarModelDetail {
  ModelDetailNo: string;
  ModelDetailName: string;
  ModelNo: string;
}

export interface CarGrade {
  GradeNo: string;
  GradeName: string;
  ModelDetailNo: string;
}

export interface CarGradeDetail {
  GradeDetailNo: string;
  GradeDetailName: string;
  GradeNo: string;
}

export interface CarColor {
  CKeyNo: string;
  ColorName: string;
}

export interface CarFuel {
  FKeyNo: string;
  FuelName: string;
}

export interface CarMission {
  MKeyNo: string;
  MissionName: string;
}

export interface CarOption {
  CarOptionNo: number;
  CarOptionName: string;
  CarOptionGroupName: string;
}

export interface FilterData {
  makers: CarMaker[];
  models: Record<string, CarModel[]>;
  modelDetails: Record<string, CarModelDetail[]>;
  grades: Record<string, CarGrade[]>;
  gradeDetails: Record<string, CarGradeDetail[]>;
  colors: CarColor[];
  fuels: CarFuel[];
  missions: CarMission[];
  categories?: { value: string; label: string }[];
}

export interface CarListingParams {
  carnation?: string;
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
  carNumber: string;
  options: { group: string; items: string[] }[];
  dealer: string;
  phone: string;
  diagnosticsUrl?: string | null;
  blurDataUrl?: string;
}
