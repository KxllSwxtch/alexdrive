function reLoadJsonCarDataMulti(CarMode, Page, PageSize) {
  // danji search
  if (Page == null || Page == "") Page = 1;

  var vPageRowCount = jQuery.trim($("#sbxPageRowCount").val());
  var vPageAscDesc = jQuery.trim($("#sbxPageAscDesc").val());
  var vPageSort = jQuery.trim($("#sbxPageSort").val());

  //가격순지정시 오름차순으로 변경요청 - 이정찬부장님.
  if (vPageSort == "2") {
    if ($("#isAscDesc").val() == "1") {
      $("#sbxPageAscDesc").val("0");
      vPageAscDesc = "0";
      $("#isAscDesc").val("2");
      $("#sbxPageAscDesc").val("0").selectbox("detach").selectbox("attach");
    }
  }

  //멀티 시도지역
  var vSearchSiDo = "";
  var vSearchSiDoArea = "";
  var vSearchDanji = jQuery.trim($("#cbxSearchDanji").val());
  //2021-04-30 사업부 수원 중앙 + 신중앙 + 남수원 = 중앙남수원 요청으로인한 1차 하드코딩
  if (vSearchDanji.indexOf("92102") > -1) {
    vSearchDanji = vSearchDanji + ",92106,92109";
  }
  //2021-06-18 사업부 기존 경매서수원 을 중앙남수원 처럼 변경해달라는 요청으로인한 1차 하드코딩
  if (vSearchDanji.indexOf("92101") > -1) {
    vSearchDanji = vSearchDanji + ",92105";
  }
  vSearchSiDo = jQuery.trim($("#searchSiDo_multi").val());

  var allcheckArea = $("#searchSiDoArea_multi")
    .next()
    .children()
    .find("li")
    .eq(0)
    .find("input")
    .is(":checked");
  if (!allcheckArea) {
    vSearchSiDoArea = jQuery.trim($("#searchSiDoArea_multi").val());
  }
  $("#cbxSearchSiDo").val(vSearchSiDo);
  $("#cbxSearchSiDoArea").val(vSearchSiDoArea);

  // car search
  var vSearchMaker = parseInt(jQuery.trim($("#tbxSearchMaker").val()));
  var vSearchModel = parseInt(jQuery.trim($("#tbxSearchModel").val()));
  var vSearchModelDetail = jQuery.trim($("#tbxSearchModelDetail").val());
  var vSearchGrade = jQuery.trim($("#tbxSearchGrade").val());
  var vSearchGradeDetail = jQuery.trim($("#tbxSearchGradeDetail").val());

  var vSearchMakeSYear = jQuery.trim($("#cbxSearchMakeSYear").val());
  var vSearchMakeSMonth = jQuery.trim($("#cbxSearchMakeSDay").val());

  var vSearchMakeEYear = jQuery.trim($("#cbxSearchMakeEYear").val());
  var vSearchMakeEMonth = jQuery.trim($("#cbxSearchMakeEDay").val());

  var vSearchMakeSDay = "";
  var vSearchMakeEDay = "";

  if (vSearchMakeSYear.length == 4) {
  }

  if (vSearchMakeSYear.length == 4) {
    if (vSearchMakeSMonth.length > 0) {
      vSearchMakeSDay = vSearchMakeSYear + "-" + vSearchMakeSMonth;
    } else {
      vSearchMakeSDay = vSearchMakeSYear + "-01";
    }
  }

  if (vSearchMakeEYear.length == 4) {
    if (vSearchMakeEMonth.length > 0) {
      vSearchMakeEDay = vSearchMakeEYear + "-" + vSearchMakeEMonth;
    } else {
      vSearchMakeEDay = vSearchMakeEYear + "-12";
    }
  }

  vSearchMakeSDay = vSearchMakeSDay.length == 7 ? vSearchMakeSDay : "";
  vSearchMakeEDay = vSearchMakeEDay.length == 7 ? vSearchMakeEDay : "";

  var vSearchDriveS = parseInt(jQuery.trim($("#cbxSearchDriveS").val()));
  var vSearchDriveE = parseInt(jQuery.trim($("#cbxSearchDriveE").val()));
  if ($("input:checkbox[id='cbxSearchKmCheck']").is(":checked") == true) {
    vSearchDriveS = parseInt(jQuery.trim($("#tbxSearchDriveSI").val()));
    vSearchDriveE = parseInt(jQuery.trim($("#tbxSearchDriveEI").val()));
    if (vSearchDriveS) $("#cbxSearchDriveS").val(vSearchDriveS);
    if (vSearchDriveE) $("#cbxSearchDriveS").val(vSearchDriveE);
  }

  var vSearchMission = jQuery.trim($("#cbxSearchMission").val());
  var vSearchFuel = jQuery.trim($("#cbxSearchFuel").val());
  var vSearchColor = jQuery.trim($("#cbxSearchColor").val());

  var vSearchMoneyS = parseInt(jQuery.trim($("#cbxSearchMoneyS").val()));
  var vSearchMoneyE = parseInt(jQuery.trim($("#cbxSearchMoneyE").val()));
  if ($("input:checkbox[id='cbxSearchMoneyCheck']").is(":checked") == true) {
    vSearchMoneyS = parseInt(jQuery.trim($("#tbxSearchMoneySI").val()));
    vSearchMoneyE = parseInt(jQuery.trim($("#tbxSearchMoneyEI").val()));
    if (vSearchMoneyS) $("#cbxSearchMoneyS").val(vSearchMoneyS);
    if (vSearchMoneyE) $("#cbxSearchMoneyE").val(vSearchMoneyE);
  }

  var vSearchIsLPG = $("#cbxSearchIsLPG").prop("checked") ? "True" : "False";
  var vSearchIsSago = $("#cbxSearchIsSago").prop("checked") ? "True" : "False";
  var cbxSearchIsCarPhoto = $("#cbxSearchIsCarPhoto").prop("checked")
    ? "True"
    : "False";
  var vSearchIsSaleAmount = $("#cbxSearchIsSaleAmount").prop("checked")
    ? "True"
    : "False";
  var vSearchIsCarCheck = $("#cbxSearchIsCarCheck").prop("checked")
    ? "True"
    : "False";
  var vSearchIsLeaseCheck = $("#cbxSearchIsLeaseCheck").prop("checked")
    ? "True"
    : "False";

  // quick search
  var vSearchCarName = jQuery.trim($("#tbxSearchCarName").val());
  var vSearchDealer = jQuery.trim($("#tbxSearchDealer").val());
  var vSearchShop = jQuery.trim($("#tbxSearchShop").val());
  var vSearchHP = jQuery.trim($("#tbxSearchHP").val().replace(/\-/g, ""));
  var vSearchCarNumber = jQuery.trim($("#tbxSearchCarNumber").val());
  var vSearchCarOption = jQuery.trim($("#cbxSearchOption").val());
  var vSearchCarTruckTonS = jQuery.trim($("#sbxCarTruckTonS").val());
  var vSearchCarTruckTonE = jQuery.trim($("#sbxCarTruckTonE").val());
  //전체해제
  if (
    vSearchSiDo == "0" &&
    vSearchSiDoArea == "" &&
    vSearchDanji == "" &&
    isNaN(vSearchMaker) &&
    isNaN(vSearchModel) &&
    vSearchModelDetail == "" &&
    vSearchGrade == "" &&
    vSearchGradeDetail == "" &&
    vSearchMakeSDay == "" &&
    vSearchMakeEDay == "" &&
    isNaN(vSearchDriveS) &&
    isNaN(vSearchDriveE) &&
    vSearchMission == "" &&
    vSearchFuel == "" &&
    vSearchColor == "" &&
    isNaN(vSearchMoneyS) &&
    isNaN(vSearchMoneyE) &&
    vSearchIsLPG == "False" &&
    vSearchIsSago == "False" &&
    cbxSearchIsCarPhoto == "False" &&
    vSearchIsSaleAmount == "False" &&
    vSearchIsCarCheck == "False" &&
    vSearchIsLeaseCheck == "False" &&
    vSearchCarName == "" &&
    vSearchDealer == "" &&
    vSearchShop == "" &&
    vSearchHP == "" &&
    vSearchCarNumber == "" &&
    vSearchCarOption == ""
  ) {
    alert(
      "차량 전체 검색은 지원하지 않습니다.\r\n검색 조건을 하나이상 선택 및 입력하세요.",
    );
    setTimeout(function () {
      if (vLoading.css("display") == "block") {
        vLoading.fadeOut("slow");
      }
    }, 1000);
    return;
  }
  var dataPara = {
    para: {
      PageNow: Page,
      PageSize: vPageRowCount,
      PageSort: vPageSort,
      PageAscDesc: vPageAscDesc,
      CarMode: CarMode,

      CarSiDoNo: vSearchSiDo,
      CarSiDoAreaNo: vSearchSiDoArea,
      CarDanjiNo: vSearchDanji,
      CarMakerNo: vSearchMaker,
      CarModelNo: vSearchModel,
      CarModelDetailNo: vSearchModelDetail,
      CarGradeNo: vSearchGrade,
      CarGradeDetailNo: vSearchGradeDetail,

      CarMakeSDate: vSearchMakeSDay,
      CarMakeEDate: vSearchMakeEDay,
      CarDriveSKm: vSearchDriveS,
      CarDriveEKm: vSearchDriveE,

      CarMission: vSearchMission,
      CarFuel: vSearchFuel,
      CarColor: vSearchColor,
      CarSMoney: vSearchMoneyS,
      CarEMoney: vSearchMoneyE,

      CarIsLPG: vSearchIsLPG,
      CarIsSago: vSearchIsSago,
      CarIsPhoto: cbxSearchIsCarPhoto,
      CarIsSaleAmount: vSearchIsSaleAmount,
      CarIsCarCheck: vSearchIsCarCheck,
      CarIsLeaseCheck: vSearchIsLeaseCheck,

      CarName: vSearchCarName,
      CarDealerName: vSearchDealer,
      CarShopName: vSearchShop,
      CarDealerHP: vSearchHP,
      CarNumber: vSearchCarNumber,
      CarOption: vSearchCarOption,

      CarTruckTonS: vSearchCarTruckTonS,
      CarTruckTonE: vSearchCarTruckTonE,
    },
  };
  var Url = "/Car/DataPart";
  $.ajax({
    type: "POST",
    cache: false,
    contentType: "application/json; charset=utf-8",
    url: Url,
    data: JSON.stringify(dataPara),
    dataType: "html",
    success: function (arrData) {
      $("#ui_context").html(arrData);
      vLoading.fadeOut("slow");

      // 이벤트를 등록 합니다.
      reSetEventCarOptionView();
      reSetEventCarThumbView();
    },
    fail: function (data) {
      alert(
        "제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.",
      );
      return;
    },
  }).done(function () {
    if (vLoading.css("display") == "block") {
      //vLoading.fadeOut("slow");
    }
  });
}
function reLoadJsonCarDataCs(CarMode, Page, PageSize) {
  // danji search
  if (Page == null || Page == "") Page = 1;

  var vPageRowCount = jQuery.trim($("#sbxPageRowCount").val());
  var vPageAscDesc = jQuery.trim($("#sbxPageAscDesc").val());
  var vPageSort = jQuery.trim($("#sbxPageSort").val());

  //가격순지정시 오름차순으로 변경요청 - 이정찬부장님.
  if (vPageSort == "2") {
    if ($("#isAscDesc").val() == "1") {
      $("#sbxPageAscDesc").val("0");
      vPageAscDesc = "0";
      $("#isAscDesc").val("2");
      $("#sbxPageAscDesc").val("0").selectbox("detach").selectbox("attach");
    }
  }

  //멀티 시도지역
  var vSearchSiDo = "";
  var vSearchSiDoArea = "";
  var vSearchDanji = "";

  var allcheckSido = $("#searchSiDo_multi")
    .next()
    .children()
    .find("li")
    .eq(0)
    .find("input")
    .is(":checked");
  if (!allcheckSido) {
    vSearchSiDo = jQuery.trim($("#searchSiDo_multi").val());
  }

  var allcheckArea = $("#searchSiDoArea_multi")
    .next()
    .children()
    .find("li")
    .eq(0)
    .find("input")
    .is(":checked");
  if (!allcheckArea) {
    vSearchSiDoArea = jQuery.trim($("#searchSiDoArea_multi").val());
  }

  var allcheckDanji = $("#searchDanji_multi")
    .next()
    .children()
    .find("li")
    .eq(0)
    .find("input")
    .is(":checked");
  if (!allcheckDanji) {
    vSearchDanji = jQuery.trim($("#searchDanji_multi").val());
    //2021-04-30 사업부 수원 중앙 + 신중앙 + 남수원 = 중앙남수원 요청으로인한 1차 하드코딩
    if (vSearchDanji.indexOf("92102") > -1) {
      vSearchDanji = vSearchDanji + ",92106,92109";
    }
    //2021-06-18 사업부 기존 경매서수원 을 중앙남수원 처럼 변경해달라는 요청으로인한 1차 하드코딩
    if (vSearchDanji.indexOf("92101") > -1) {
      vSearchDanji = vSearchDanji + ",92105";
    }
  }

  $("#cbxSearchSiDo").val(vSearchSiDo);
  $("#cbxSearchSiDoArea").val(vSearchSiDoArea);
  $("#cbxSearchDanji").val(vSearchDanji);
  // car search
  var vSearchCountry = parseInt(jQuery.trim($("#searchCountry_multi").val()));
  var vSearchMaker = parseInt(jQuery.trim($("#searchMaker_multi").val()));
  var vSearchModel = parseInt(jQuery.trim($("#searchModel_multi").val()));
  var vSearchModelDetail = jQuery.trim($("#searchModelDetail_multi").val());
  var vSearchGrade = jQuery.trim($("#searchGrade_multi").val());
  var vSearchGradeDetail = jQuery.trim($("#searchGradeDetail_multi").val());

  var vSearchMakeSYear = jQuery.trim($("#cbxSearchMakeSYear").val());
  var vSearchMakeSMonth = jQuery.trim($("#cbxSearchMakeSDay").val());

  var vSearchMakeEYear = jQuery.trim($("#cbxSearchMakeEYear").val());
  var vSearchMakeEMonth = jQuery.trim($("#cbxSearchMakeEDay").val());

  var vSearchMakeSDay = "";
  var vSearchMakeEDay = "";

  //나라만 찍혀있을경우.
  if (!isNaN(vSearchCountry) && isNaN(vSearchMaker)) {
    var arrData = Bizjs.GetMakerBase(vSearchCountry);

    var countryMaker = new Array();

    for (var row = 0; row < arrData.length; row++) {
      var vno = arrData[row].MakerNo;
      countryMaker.push(vno);
    }

    if (countryMaker.length > 0) {
      vSearchCountry = countryMaker.join(",");
    }
  } else {
    vSearchCountry = "";
  }

  if (vSearchMakeSYear.length == 4) {
    if (vSearchMakeSMonth.length > 0) {
      vSearchMakeSDay = vSearchMakeSYear + "-" + vSearchMakeSMonth;
    } else {
      vSearchMakeSDay = vSearchMakeSYear + "-01";
    }
  }

  if (vSearchMakeEYear.length == 4) {
    if (vSearchMakeEMonth.length > 0) {
      vSearchMakeEDay = vSearchMakeEYear + "-" + vSearchMakeEMonth;
    } else {
      vSearchMakeEDay = vSearchMakeEYear + "-12";
    }
  }

  vSearchMakeSDay = vSearchMakeSDay.length == 7 ? vSearchMakeSDay : "";
  vSearchMakeEDay = vSearchMakeEDay.length == 7 ? vSearchMakeEDay : "";

  var vSearchDriveS = parseInt(jQuery.trim($("#cbxSearchDriveS").val()));
  var vSearchDriveE = parseInt(jQuery.trim($("#cbxSearchDriveE").val()));
  if ($("input:checkbox[id='cbxSearchKmCheck']").is(":checked") == true) {
    vSearchDriveS = parseInt(jQuery.trim($("#tbxSearchDriveSI").val()));
    vSearchDriveE = parseInt(jQuery.trim($("#tbxSearchDriveEI").val()));
    if (vSearchDriveS) $("#cbxSearchDriveS").val(vSearchDriveS);
    if (vSearchDriveE) $("#cbxSearchDriveS").val(vSearchDriveE);
  }

  var vSearchMission = jQuery.trim($("#cbxSearchMission").val());
  var vSearchFuel = jQuery.trim($("#cbxSearchFuel").val());
  var vSearchColor = jQuery.trim($("#cbxSearchColor").val());

  var vSearchMoneyS = parseInt(jQuery.trim($("#cbxSearchMoneyS").val()));
  var vSearchMoneyE = parseInt(jQuery.trim($("#cbxSearchMoneyE").val()));
  if ($("input:checkbox[id='cbxSearchMoneyCheck']").is(":checked") == true) {
    vSearchMoneyS = parseInt(jQuery.trim($("#tbxSearchMoneySI").val()));
    vSearchMoneyE = parseInt(jQuery.trim($("#tbxSearchMoneyEI").val()));
    if (vSearchMoneyS) $("#cbxSearchMoneyS").val(vSearchMoneyS);
    if (vSearchMoneyE) $("#cbxSearchMoneyE").val(vSearchMoneyE);
  }
  //var vsearchJesiCheck = $("#cbxJesiCheck").val();

  var vSearchIsLPG = $("#cbxSearchIsLPG").prop("checked") ? "True" : "False";
  var vSearchIsSago = $("#cbxSearchIsSago").prop("checked") ? "True" : "False";
  var cbxSearchIsCarPhoto = $("#cbxSearchIsCarPhoto").prop("checked")
    ? "True"
    : "False";
  var vSearchIsSaleAmount = $("#cbxSearchIsSaleAmount").prop("checked")
    ? "True"
    : "False";
  var vSearchIsCarCheck = $("#cbxSearchIsCarCheck").prop("checked")
    ? "True"
    : "False";
  var vSearchIsLeaseCheck = $("#cbxSearchIsLeaseCheck").prop("checked")
    ? "True"
    : "False";

  // quick search
  var vSearchCarName = jQuery.trim($("#tbxSearchCarName").val());
  var vSearchDealer = jQuery.trim($("#tbxSearchDealer").val());
  var vSearchShop = jQuery.trim($("#tbxSearchShop").val());
  var vSearchHP = jQuery.trim($("#tbxSearchHP").val().replace(/\-/g, ""));
  var vSearchCarNumber = jQuery.trim($("#tbxSearchCarNumber").val());
  var vSearchCarOption = jQuery.trim($("#cbxSearchOption").val());
  var vSearchCarTruckTonS = jQuery.trim($("#sbxCarTruckTonS").val());
  var vSearchCarTruckTonE = jQuery.trim($("#sbxCarTruckTonE").val());
  //전체해제
  if (
    vSearchSiDo == "0" &&
    vSearchSiDoArea == "" &&
    vSearchDanji == "" &&
    isNaN(vSearchCountry) &&
    isNaN(vSearchMaker) &&
    isNaN(vSearchModel) &&
    vSearchModelDetail == "" &&
    vSearchGrade == "" &&
    vSearchGradeDetail == "" &&
    vSearchMakeSDay == "" &&
    vSearchMakeEDay == "" &&
    isNaN(vSearchDriveS) &&
    isNaN(vSearchDriveE) &&
    vSearchMission == "" &&
    vSearchFuel == "" &&
    vSearchColor == "" &&
    isNaN(vSearchMoneyS) &&
    isNaN(vSearchMoneyE) &&
    vSearchIsLPG == "False" &&
    vSearchIsSago == "False" &&
    cbxSearchIsCarPhoto == "False" &&
    vSearchIsSaleAmount == "False" &&
    vSearchIsCarCheck == "False" &&
    vSearchIsLeaseCheck == "False" &&
    vSearchCarName == "" &&
    vSearchDealer == "" &&
    vSearchShop == "" &&
    vSearchHP == "" &&
    vSearchCarNumber == "" &&
    vSearchCarOption == ""
  ) {
    alert(
      "차량 전체 검색은 지원하지 않습니다.\r\n검색 조건을 하나이상 선택 및 입력하세요.",
    );
    setTimeout(function () {
      if (vLoading.css("display") == "block") {
        vLoading.fadeOut("slow");
      }
    }, 1000);
    return;
  }

  var dataPara = {
    para: {
      PageNow: Page,
      PageSize: vPageRowCount,
      PageSort: vPageSort,
      PageAscDesc: vPageAscDesc,
      CarMode: CarMode,

      CarSiDoNo: vSearchSiDo,
      CarSiDoAreaNo: vSearchSiDoArea,
      CarDanjiNo: vSearchDanji,
      CarCountryMaker: vSearchCountry,
      CarMakerNo: vSearchMaker,
      CarModelNo: vSearchModel,
      CarModelDetailNo: vSearchModelDetail,
      CarGradeNo: vSearchGrade,
      CarGradeDetailNo: vSearchGradeDetail,

      CarMakeSDate: vSearchMakeSDay,
      CarMakeEDate: vSearchMakeEDay,
      CarDriveSKm: vSearchDriveS,
      CarDriveEKm: vSearchDriveE,

      CarMission: vSearchMission,
      CarFuel: vSearchFuel,
      CarColor: vSearchColor,
      CarSMoney: vSearchMoneyS,
      CarEMoney: vSearchMoneyE,

      CarIsLPG: vSearchIsLPG,
      CarIsSago: vSearchIsSago,
      CarIsPhoto: cbxSearchIsCarPhoto,
      CarIsSaleAmount: vSearchIsSaleAmount,
      CarIsCarCheck: vSearchIsCarCheck,
      CarIsLeaseCheck: vSearchIsLeaseCheck,

      CarName: vSearchCarName,
      CarDealerName: vSearchDealer,
      CarShopName: vSearchShop,
      CarDealerHP: vSearchHP,
      CarNumber: vSearchCarNumber,
      CarOption: vSearchCarOption,

      CarTruckTonS: vSearchCarTruckTonS,
      CarTruckTonE: vSearchCarTruckTonE,
    },
  };

  var Url = "/Car/DataPart";
  $.ajax({
    type: "POST",
    cache: false,
    contentType: "application/json; charset=utf-8",
    url: Url,
    data: JSON.stringify(dataPara),
    dataType: "html",
    success: function (arrData) {
      $("#ui_context").html(arrData);
      vLoading.fadeOut("slow");

      // 이벤트를 등록 합니다.
      reSetEventCarOptionView();
      reSetEventCarThumbView();
    },
    fail: function (data) {
      alert(
        "제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.",
      );
      return;
    },
  }).done(function () {
    if (vLoading.css("display") == "block") {
      vLoading.fadeOut("slow");
    }
  });
}

function reLoadPage(totalCount, PageSize, Page, PageArea, CarMode) {
  var innerHtml = "";

  if (totalCount > 0) {
    var totalPage = parseInt(totalCount / PageSize);
    if (totalCount % PageSize > 0) totalPage++;

    var prePage = (parseInt((Page - 1) / PageArea) - 1) * PageArea + 1;
    var nexPage = (parseInt((Page - 1) / PageArea) + 1) * PageArea + 1;

    prePage = prePage < 0 ? 1 : prePage;
    nexPage = totalPage < nexPage ? totalPage : nexPage;

    /* 페이징 구성 */
    innerHtml += "<table>";
    innerHtml += "<tr>";

    if (Page == 1)
      innerHtml += "<th><img src='/include/image/page/btn_first.gif' /></th>";
    else
      innerHtml +=
        "<th class='uc_btnmode' onclick='goPageSubmit(1);'><img src='/include/image/page/btn_first.gif' /></th>";

    if (totalPage > 0)
      innerHtml +=
        "<th class='uc_btnmode' onclick='goPageSubmit(" +
        prePage +
        ");'><img src='/include/image/page/btn_prev.gif' /></th>";

    for (var ipage = 0; ipage < totalPage && ipage < PageArea; ipage++) {
      var ipagenow = ipage + parseInt((Page - 1) / PageArea) * PageArea + 1;
      if (ipagenow <= totalPage) {
        if (ipagenow == Page) {
          innerHtml += "<td class='uc_choose'>" + ipagenow + "</td>";
        } else {
          innerHtml +=
            "<td class='uc_btnmode' onclick='goPageSubmit(" +
            ipagenow +
            ");'>" +
            ipagenow +
            "</td>";
        }
      }
    }

    // 마지막
    if (totalPage > 0) {
      innerHtml +=
        "<th class='uc_btnmode' onclick='goPageSubmit(" +
        nexPage +
        ");'><img src='/include/image/page/btn_next.gif' /></th>";
    }

    innerHtml += "</tr>";
    innerHtml += "</table>";
  }
  $(".uc_cpage").html(innerHtml);
  vLoading.fadeOut("slow");
}

function goFormSubmit(page) {
  goPageSubmit(page);
}
function goPageSubmit(Page) {
  try {
    //$("#evPop").hide();
    $("#evPop").fadeOut("slow");
    var defaultSelectChange = false;
    defaultSelectChange = carOptionArrOrEmpty();
    var vSrCarName = $("#tbxSearchCarName").val();
    var vSrDealer = $("#tbxSearchDealer").val();
    var vSrShop = $("#tbxSearchShop").val();
    var vSrCarNumber = $("#tbxSearchCarNumber").val();
    var vSrHP = $("#tbxSearchHP").val().replace(/\-/g, "");
    if (vSrCarName.length == 1) {
      alert("등록차명은 2자 이상입력해야합니다.");
      return;
    }
    if (vSrDealer.length == 1) {
      alert("딜러명은 최소 2자이상입력해야 합니다.");
      return;
    }
    if (vSrShop.length == 1) {
      alert("상사명은 2자이상입력해야 합니다.");
      return;
    }
    if (vSrCarNumber.length > 0 && vSrCarNumber.length < 4) {
      alert("차량검색시 차량번호를 4자 이상 입력하세요!");
      return;
    }
    if (vSrHP.length > 0 && vSrHP.length < 4) {
      alert("휴대폰검색시 휴대폰번호를 4자 이상 입력하세요!");
      return;
    }

    /* check search area */
    var isSubmit = true;
    isSubmit = isSubmit && ischeckRegDayBetweenDate();
    isSubmit = isSubmit && ischeckUseKmBetweenNumber();
    isSubmit = isSubmit && ischeckCarAmountBetweenNumber();
    isSubmit = isSubmit && ischeckBetweenTruckTon();
    if (isSubmit == false) {
      return false;
    }

    $("#page").val(Page);
    vLoading.show(); // 페이지 로딩

    remakeBookMark(Page);

    var vPageSize = $("#sbxPageRowCount").val();

    if ($("#searchOptType").val() == "001") {
      reLoadJsonCarDataMulti("0", Page, vPageSize);
    } else if ($("#searchOptType").val() == "002") {
      reLoadJsonCarDataCs("0", Page, vPageSize);
    }
    regetIsPhotoCol();
  } finally {
    setTimeout(function () {
      if (vLoading.css("display") == "block") {
        vLoading.fadeOut("slow");
      }
    }, 500000);
  }
}

function goFormSubmitMulti(page) {
  goPageSubmitMulti(page);
}
function goPageSubmitMulti(Page) {
  try {
    //$("#evPop").hide();
    $("#evPop").fadeOut("slow");
    var defaultSelectChange = false;
    defaultSelectChange = carOptionArrOrEmpty();
    var vSrCarName = $("#tbxSearchCarName").val();
    var vSrDealer = $("#tbxSearchDealer").val();
    var vSrShop = $("#tbxSearchShop").val();
    var vSrCarNumber = $("#tbxSearchCarNumber").val();
    var vSrHP = $("#tbxSearchHP").val().replace(/\-/g, "");
    if (vSrCarName.length == 1) {
      alert("등록차명은 2자 이상입력해야합니다.");
      return;
    }
    if (vSrDealer.length == 1) {
      alert("딜러명은 최소 2자이상입력해야 합니다.");
      return;
    }
    if (vSrShop.length == 1) {
      alert("상사명은 2자이상입력해야 합니다.");
      return;
    }
    if (vSrCarNumber.length > 0 && vSrCarNumber.length < 4) {
      alert("차량검색시 차량번호를 4자 이상 입력하세요!");
      return;
    }
    if (vSrHP.length > 0 && vSrHP.length < 4) {
      alert("휴대폰검색시 휴대폰번호를 4자 이상 입력하세요!");
      return;
    }

    /* check search area */
    var isSubmit = true;
    isSubmit = isSubmit && ischeckRegDayBetweenDate();
    isSubmit = isSubmit && ischeckUseKmBetweenNumber();
    isSubmit = isSubmit && ischeckCarAmountBetweenNumber();
    isSubmit = isSubmit && ischeckBetweenTruckTon();
    if (isSubmit == false) {
      return false;
    }

    $("#page").val(Page);
    vLoading.show(); // 페이지 로딩

    remakeBookMark(Page);

    var vPageSize = $("#sbxPageRowCount").val();
    reLoadJsonCarDataMulti("0", Page, vPageSize);
    regetIsPhotoCol();
  } finally {
    setTimeout(function () {
      if (vLoading.css("display") == "block") {
        vLoading.fadeOut("slow");
      }
    }, 500000);
  }
}
function goFormSubmitCs(page) {
  goPageSubmitCs(page);
}
function goPageSubmitCs(Page) {
  try {
    //$("#evPop").hide();
    $("#evPop").fadeOut("slow");
    var defaultSelectChange = false;
    defaultSelectChange = carOptionArrOrEmpty();
    var vSrCarName = $("#tbxSearchCarName").val();
    var vSrDealer = $("#tbxSearchDealer").val();
    var vSrShop = $("#tbxSearchShop").val();
    var vSrCarNumber = $("#tbxSearchCarNumber").val();
    var vSrHP = $("#tbxSearchHP").val().replace(/\-/g, "");
    if (vSrCarName.length == 1) {
      alert("등록차명은 2자 이상입력해야합니다.");
      return;
    }
    if (vSrDealer.length == 1) {
      alert("딜러명은 최소 2자이상입력해야 합니다.");
      return;
    }
    if (vSrShop.length == 1) {
      alert("상사명은 2자이상입력해야 합니다.");
      return;
    }
    if (vSrCarNumber.length > 0 && vSrCarNumber.length < 4) {
      alert("차량검색시 차량번호를 4자 이상 입력하세요!");
      return;
    }
    if (vSrHP.length > 0 && vSrHP.length < 4) {
      alert("휴대폰검색시 휴대폰번호를 4자 이상 입력하세요!");
      return;
    }

    /* check search area */
    var isSubmit = true;
    isSubmit = isSubmit && ischeckRegDayBetweenDate();
    isSubmit = isSubmit && ischeckUseKmBetweenNumber();
    isSubmit = isSubmit && ischeckCarAmountBetweenNumber();
    isSubmit = isSubmit && ischeckBetweenTruckTon();
    if (isSubmit == false) {
      return false;
    }

    $("#page").val(Page);
    vLoading.show(); // 페이지 로딩

    remakeBookMark(Page);

    var vPageSize = $("#sbxPageRowCount").val();
    reLoadJsonCarDataCs("0", Page, vPageSize);
    regetIsPhotoCol();
  } finally {
    setTimeout(function () {
      if (vLoading.css("display") == "block") {
        vLoading.fadeOut("slow");
      }
    }, 500000);
  }
}

// 프린터시 파라이터 생성하기
function remakeURLPara(page) {
  var sbxPageRowCount = encodeURIComponent($("#sbxPageRowCount").val());
  var cbxSearchSiDo = $("#cbxSearchSiDo").val();
  var cbxSearchSiDoArea = encodeURIComponent($("#cbxSearchSiDoArea").val());
  var cbxSearchDanji = $("#cbxSearchDanji").val();
  var tbxSearchMaker = encodeURIComponent($("#tbxSearchMaker").val());
  var tbxSearchModel = encodeURIComponent($("#tbxSearchModel").val());
  var tbxSearchModelDetail = encodeURIComponent(
    $("#tbxSearchModelDetail").val(),
  );
  var tbxSearchGrade = encodeURIComponent($("#tbxSearchGrade").val());
  var tbxSearchGradeDetail = encodeURIComponent(
    $("#tbxSearchGradeDetail").val(),
  );

  var cbxSearchMakeSYear = encodeURIComponent($("#cbxSearchMakeSYear").val());
  var cbxSearchMakeSDay = encodeURIComponent($("#cbxSearchMakeSDay").val());
  var cbxSearchMakeEYear = encodeURIComponent($("#cbxSearchMakeEYear").val());
  var cbxSearchMakeEDay = encodeURIComponent($("#cbxSearchMakeEDay").val());
  var cbxSearchDriveS = encodeURIComponent($("#cbxSearchDriveS").val());
  var cbxSearchDriveE = encodeURIComponent($("#cbxSearchDriveE").val());
  if ($("input:checkbox[id='cbxSearchKmCheck']").is(":checked") == true) {
    cbxSearchDriveS = encodeURIComponent($("#tbxSearchDriveSI").val());
    cbxSearchDriveE = encodeURIComponent($("#tbxSearchDriveEI").val());
  }

  var cbxSearchMission = encodeURIComponent($("#cbxSearchMission").val());
  var cbxSearchFuel = encodeURIComponent($("#cbxSearchFuel").val());
  var cbxSearchColor = encodeURIComponent($("#cbxSearchColor").val());
  var cbxSearchMoneyS = encodeURIComponent($("#cbxSearchMoneyS").val());
  var cbxSearchMoneyE = encodeURIComponent($("#cbxSearchMoneyE").val());
  if ($("input:checkbox[id='cbxSearchKmCheck']").is(":checked") == true) {
    cbxSearchMoneyS = encodeURIComponent($("#tbxSearchMoneySI").val());
    cbxSearchMoneyE = encodeURIComponent($("#tbxSearchMoneyEI").val());
  }

  var cbxSearchIsLPG = encodeURIComponent(
    $("#cbxSearchIsLPG").is(":checked") ? "on" : "",
  );
  var cbxSearchIsSago = encodeURIComponent(
    $("#cbxSearchIsSago").is(":checked") ? "on" : "",
  );
  var cbxSearchIsCarPhoto = encodeURIComponent(
    $("#cbxSearchIsCarPhoto").is(":checked") ? "on" : "",
  );
  var cbxSearchIsSaleAmount = encodeURIComponent(
    $("#cbxSearchIsSaleAmount").is(":checked") ? "on" : "",
  );
  var cbxSearchIsCarCheck = encodeURIComponent(
    $("#cbxSearchIsCarCheck").is(":checked") ? "on" : "",
  );
  var cbxSearchIsLeaseCheck = encodeURIComponent(
    $("#cbxSearchIsLeaseCheck").is(":checked") ? "on" : "",
  );

  var tbxSearchCarName = encodeURIComponent($("#tbxSearchCarName").val());
  var tbxSearchDealer = encodeURIComponent($("#tbxSearchDealer").val());
  var tbxSearchShop = encodeURIComponent($("#tbxSearchShop").val());
  var tbxSearchHP = encodeURIComponent($("#tbxSearchHP").val());
  var tbxSearchCarNumber = encodeURIComponent($("#tbxSearchCarNumber").val());
  var cbxSearchOption = encodeURIComponent($("#cbxSearchOption").val());

  // 쿠키 값에 담고 서브밋 하기
  var urlPara = {
    page: page,
    sbxPageRowCount: sbxPageRowCount,
    cbxSearchSiDo: cbxSearchSiDo,
    cbxSearchSiDoArea: cbxSearchSiDoArea,
    cbxSearchDanji: cbxSearchDanji,
    tbxSearchMaker: tbxSearchMaker,
    tbxSearchModel: tbxSearchModel,
    tbxSearchModelDetail: tbxSearchModelDetail,
    tbxSearchGrade: tbxSearchGrade,
    tbxSearchGradeDetail: tbxSearchGradeDetail,

    cbxSearchMakeSYear: cbxSearchMakeSYear,
    cbxSearchMakeSDay: cbxSearchMakeSDay,
    cbxSearchMakeEYear: cbxSearchMakeEYear,
    cbxSearchMakeEDay: cbxSearchMakeEDay,
    cbxSearchDriveS: cbxSearchDriveS,
    cbxSearchDriveE: cbxSearchDriveE,
    cbxSearchMission: cbxSearchMission,
    cbxSearchFuel: cbxSearchFuel,
    cbxSearchColor: cbxSearchColor,
    cbxSearchMoneyS: cbxSearchMoneyS,
    cbxSearchMoneyE: cbxSearchMoneyE,
    cbxSearchIsLPG: cbxSearchIsLPG,
    cbxSearchIsSago: cbxSearchIsSago,
    cbxSearchIsCarPhoto: cbxSearchIsCarPhoto,
    cbxSearchIsSaleAmount: cbxSearchIsSaleAmount,
    cbxSearchIsCarCheck: cbxSearchIsCarCheck,
    cbxSearchIsLeaseCheck: cbxSearchIsLeaseCheck,
    tbxSearchCarName: tbxSearchCarName,
    tbxSearchDealer: tbxSearchDealer,
    tbxSearchShop: tbxSearchShop,
    tbxSearchHP: tbxSearchHP,
    tbxSearchCarNumber: tbxSearchCarNumber,
    cbxSearchOption: cbxSearchOption,
  };

  return $.param(urlPara);
}

// 북마크 파라미터 기억
function remakeBookMark(page) {
  // 쿠키 값에 담고 서브밋 하기
  var sbxPageRowCount = $("#sbxPageRowCount").val();
  var sbxPageSort = $("#sbxPageSort").val();
  var sbxPageAscDesc = $("#sbxPageAscDesc").val();

  //가격순지정시 오름차순으로 변경요청 - 이정찬부장님.
  if (sbxPageSort == "2") {
    if ($("#isAscDesc").val() == "1") {
      $("#sbxPageAscDesc").val("0");
      sbxPageAscDesc = "0";
      //$("#isAscDesc").val("2");
    }
  }

  var cbxSearchSiDo = $("#cbxSearchSiDo").val();
  var cbxSearchSiDoArea = $("#cbxSearchSiDoArea").val();
  var cbxSearchDanji = $("#cbxSearchDanji").val();
  var tbxSearchMaker = $("#tbxSearchMaker").val();
  var tbxSearchModel = $("#tbxSearchModel").val();
  var tbxSearchModelDetail = $("#tbxSearchModelDetail").val();
  var tbxSearchGrade = $("#tbxSearchGrade").val();
  var tbxSearchGradeDetail = $("#tbxSearchGradeDetail").val();

  var cbxSearchMakeSYear = $("#cbxSearchMakeSYear").val();
  var cbxSearchMakeSDay = $("#cbxSearchMakeSDay").val();
  var cbxSearchMakeEYear = $("#cbxSearchMakeEYear").val();
  var cbxSearchMakeEDay = $("#cbxSearchMakeEDay").val();
  var cbxSearchDriveS = $("#cbxSearchDriveS").val();
  var cbxSearchDriveE = $("#cbxSearchDriveE").val();

  var cbxSearchMission = $("#cbxSearchMission").val();
  var cbxSearchFuel = $("#cbxSearchFuel").val();
  var cbxSearchColor = $("#cbxSearchColor").val();
  var cbxSearchMoneyS = $("#cbxSearchMoneyS").val();
  var cbxSearchMoneyE = $("#cbxSearchMoneyE").val();

  var cbxSearchIsLPG = $("#cbxSearchIsLPG").is(":checked") ? "on" : "";
  var cbxSearchIsSago = $("#cbxSearchIsSago").is(":checked") ? "on" : "";
  var cbxSearchIsCarPhoto = $("#cbxSearchIsCarPhoto").is(":checked")
    ? "on"
    : "";
  var cbxSearchIsSaleAmount = $("#cbxSearchIsSaleAmount").is(":checked")
    ? "on"
    : "";
  var cbxSearchIsCarCheck = $("#cbxSearchIsCarCheck").is(":checked")
    ? "on"
    : "";

  var tbxSearchCarName = $("#tbxSearchCarName").val();
  var tbxSearchDealer = $("#tbxSearchDealer").val();
  var tbxSearchShop = $("#tbxSearchShop").val();
  var tbxSearchHP = $("#tbxSearchHP").val();
  var tbxSearchCarNumber = $("#tbxSearchCarNumber").val();
  var cbxSearchOption = $("#cbxSearchOption").val();

  // 쿠키 값에 담고 서브밋 하기
  var urlPara = {
    page: page,
    sbxPageRowCount: sbxPageRowCount,
    sbxPageSort: sbxPageSort,
    sbxPageAscDesc: sbxPageAscDesc,
    cbxSearchSiDo: cbxSearchSiDo,
    cbxSearchSiDoArea: cbxSearchSiDoArea,
    cbxSearchDanji: cbxSearchDanji,
    tbxSearchMaker: tbxSearchMaker,
    tbxSearchModel: tbxSearchModel,
    tbxSearchModelDetail: tbxSearchModelDetail,
    tbxSearchGrade: tbxSearchGrade,
    tbxSearchGradeDetail: tbxSearchGradeDetail,

    cbxSearchMakeSYear: cbxSearchMakeSYear,
    cbxSearchMakeSDay: cbxSearchMakeSDay,
    cbxSearchMakeEYear: cbxSearchMakeEYear,
    cbxSearchMakeEDay: cbxSearchMakeEDay,
    cbxSearchDriveS: cbxSearchDriveS,
    cbxSearchDriveE: cbxSearchDriveE,
    cbxSearchMission: cbxSearchMission,
    cbxSearchFuel: cbxSearchFuel,
    cbxSearchColor: cbxSearchColor,
    cbxSearchMoneyS: cbxSearchMoneyS,
    cbxSearchMoneyE: cbxSearchMoneyE,
    cbxSearchIsLPG: cbxSearchIsLPG,
    cbxSearchIsSago: cbxSearchIsSago,
    cbxSearchIsCarPhoto: cbxSearchIsCarPhoto,
    cbxSearchIsSaleAmount: cbxSearchIsSaleAmount,
    cbxSearchIsCarCheck: cbxSearchIsCarCheck,
    tbxSearchCarName: tbxSearchCarName,
    tbxSearchDealer: tbxSearchDealer,
    tbxSearchShop: tbxSearchShop,
    tbxSearchHP: tbxSearchHP,
    tbxSearchCarNumber: tbxSearchCarNumber,
    cbxSearchOption: cbxSearchOption,
  };

  setFooterBookMark("101", "매물조회", "/Car/Data", $.param(urlPara));
}

// 포토 뷰 설정
function reSetIsPhotoCol() {
  //정다은 : 2016-10-06
  //이미지 보기에서 규칙성 검사를 하지 않고 바로 검색을 하기때문에 검색조건 추가
  var vSrCarName = $("#tbxSearchCarName").val();
  var vSrDealer = $("#tbxSearchDealer").val();
  var vSrShop = $("#tbxSearchShop").val();
  var vSrCarNumber = $("#tbxSearchCarNumber").val();
  var vSrHP = $("#tbxSearchHP").val();
  if (vSrCarName.length == 1) {
    alert("등록차명은 2자 이상입력해야합니다.");
    return;
  }
  if (vSrDealer.length == 1) {
    alert("딜러명은 최소 2자이상입력해야 합니다.");
    return;
  }
  if (vSrShop.length == 1) {
    alert("상사명은 2자이상입력해야 합니다.");
    return;
  }
  if (vSrCarNumber.length > 0 && vSrCarNumber.length < 4) {
    alert("차량검색시 차량번호를 4자 이상 입력하세요!");
    return;
  }
  if (vSrHP.length > 0 && vSrHP.length < 4) {
    alert("휴대폰검색시 휴대폰번호를 4자 이상 입력하세요!");
    return;
  }

  /* check search area */
  var isSubmit = true;
  isSubmit = isSubmit && ischeckRegDayBetweenDate();
  isSubmit = isSubmit && ischeckUseKmBetweenNumber();
  isSubmit = isSubmit && ischeckCarAmountBetweenNumber();

  if (isSubmit == false) {
    return;
  }
  var isPhotoCol = $.cookie("MODE_PHOTO_VIEW");

  if (isPhotoCol != "1" || isPhotoCol == undefined) {
    $.cookie("MODE_PHOTO_VIEW", "1"); //, { domain: 'dicar.co.kr' }
  } else {
    $.cookie("MODE_PHOTO_VIEW", "", { expires: -1 }); // , domain: 'dicar.co.kr'
  }

  $("form").submit();
}
function regetIsPhotoCol() {
  var isPhotoCol = $.cookie("MODE_PHOTO_VIEW");
}
