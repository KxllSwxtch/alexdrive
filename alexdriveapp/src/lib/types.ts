export interface CarMaker {
  bm_no: string;
  bm_name: string;
  bm_logoImage: string;
}

export interface CarModel {
  bo_no: string;
  bo_name: string;
  bo_faceImage?: string;
  bo_startDate?: string;
  bo_endDate?: string;
  bo_group?: string;
}

export interface CarSeries {
  bs_no: string;
  bs_name: string;
  bd: CarTrim[];
}

export interface CarTrim {
  bd_no: string;
  bd_name: string;
}

export interface CarColor {
  bc_no: string;
  bc_name: string;
  bc_rgb1: string;
  bc_rgb2: string;
}

export interface FilterData {
  makers: CarMaker[];
  colors: CarColor[];
  fuels: { value: string; label: string }[];
  transmissions: { value: string; label: string }[];
}

export interface CarListingParams {
  bm_no?: string;
  bo_no?: string;
  bs_no?: string;
  bd_no?: string;
  yearFrom?: string;
  yearTo?: string;
  mileageFrom?: string;
  mileageTo?: string;
  priceFrom?: string;
  priceTo?: string;
  fuel?: string;
  transmission?: string;
  color?: string;
  keyword?: string;
  extFlag1?: string; // navigation
  extFlag2?: string; // sunroof
  extFlag3?: string; // smart key
  extFlag4?: string; // no accidents
  extFlag5?: string; // with inspection
  sort?: string;
  order?: string;
  page?: number;
  page_size?: number;
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
  priceMl?: number;
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
  priceMl?: number;
  color: string;
  carNumber: string;
  options: { group: string; items: string[] }[];
  dealer: string;
  phone: string;
  description?: string;
  info?: Record<string, string | number>;
  pricing?: Record<string, string | number>;
  specs?: Record<string, string | number>;
  inspection?: Record<string, unknown>;
}
