$(document).ready(function () {
  reSetCarMakerEvent();
  reSetCarModelEvent();
  reSetCarModelDetailEvent();
  reSetCarGradeEvent();
  // 스크롤
  reSetMakerScrollEvent();
  reSetModelScrollEvent();
  reSetModelDetailScrollEvent();
  reSetGradeScrollEvent();
  reSetGradeDetailScrollEvent();

  // 드롭다운
  reSetDropDownCountryEvent();
  reSetDropDownMakerEvent();
  reSetDropDownModelEvent();
  reSetDropDownModelDetailEvent();
  reSetDropDownGradeEvent();

  $("#btnSearchClear").click(function () {
    reSetSiDoAreaDanji();
    reSetSearch();
    reSetSearchOption();
    reSetSearchQuick();
    //reLoadCarOption();
    reLoadCarMultiOption();
    $("#truckTonFrm").hide();
    $("#kmSelectTdSelect").css("display", "block");
    $("#kmSelectTdInput").css("display", "none");
    $("#moneySelectTdSelect").css("margin-top", "3px");
    $("#moneySelectTdSelect").css("display", "block");
    $("#moneySelectTdInput").css("display", "none");
  });

  $(".uc_sido")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        $("#cbxSearchSiDo").val(val);
        $("#cbxSearchSiDoArea").val("");
        reLoadSiDoArea(val);
      },
    });
  $(".uc_sidoarea")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        $("#cbxSearchSiDoArea").val(val);
        $("#cbxSearchDanji").val("");
        reLoadDanji();
      },
    });
});

// 추후 default.js 로 이관할 내용들 : 공용데이터 가지고 오는 부분 입니다.
function jSonDataMaker() {
  return Bizjs.GetMakerBase();
  //return $.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: "/CarBase/JsonBaseCarMaker",
  //    dataType: "json"
  //});
}
function jSonDataModel(maker) {
  //return $.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: "/CarBase/JsonBaseCarModel/" + maker,
  //    dataType: "json"
  //});
  return Bizjs.GetModelBase(maker);
}
function jSonDataModelDetail(model) {
  //return $.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: "/CarBase/JsonBaseCarModelDetail/" + model,
  //    dataType: "json"
  //});
  return Bizjs.GetModelDetailBase(model);
}
function jSonDataGrade(modeldetail) {
  //return $.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: "/CarBase/JsonBaseCarGrade/" + modeldetail,
  //    dataType: "json"
  //});
  return Bizjs.GetGradeBase(modeldetail);
}
function jSonDataGradeDetail(grade) {
  //return $.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: "/CarBase/JsonBaseCarGradeDetail/" + grade,
  //    dataType: "json"
  //});
  return Bizjs.GetGradeDetailBase(grade);
}

/* car maker */
function reLoadCarMaker() {
  var vjSon = jSonDataMaker();
  reSetCarMakerData(vjSon);
  //vjSon.success(function (arrData) {
  //    reSetCarMakerData(arrData);
  //}).fail(function (ex) {
  //    alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //});
}
function reSetCarMakerData(arrData) {
  $("#sbxSearchMaker").html(""); // 초기화
  var innerHtml = "<option value=''>제조사</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].MakerNo) {
      var vno = arrData[row].MakerNo;
      var vname = arrData[row].MakerName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  if (innerHtml.length == 0)
    innerHtml = "<option value='' selected>선택</option>";

  $("#sbxSearchMaker").html(innerHtml);
  reSetCarMakerEvent();
}
function reSetCarMakerEvent() {
  // 데이터 등록 및 이벤트 등록
  $("#sbxSearchMaker").selectbox("detach");
  $("#sbxSearchMaker").selectbox({
    onChange: function (val, inst) {
      if ($("#sbxSearchMaker  option:selected").val() != "10061") {
        reLoadCarModel(val);
        reLoadCarModelDetail("");
        reLoadCarGrade("");
        reLoadCarGradeDetail("");
      } else {
        //console.log("2222b1241`412125125bbbbb");
        reSetDropDownModelListTruckSNewCar();
        //console.log("331235-3-33512-3-2353q53-3-3");
        reLoadModelDetailTruckSNewCar();
        //console.log("4-4-4-4643632462346346-4-");
        reSetDropDownModelDetailEventNewCar("truck");
      }
    },
  });
}

/* car model */
function reLoadCarModel(maker) {
  //console.log("maker::;", maker);
  var vjSon = jSonDataModel(maker);
  if (maker != "10061") {
    //console.log("1111aaaaa");
    reSetCarModelData(vjSon);
  } else {
    //console.log("2222bbbbbb");
    reSetDropDownModelListTruckSNewCar();
    //console.log("3-3-3-3-3-3-3");
    reLoadModelDetailTruckSNewCar();
    //console.log("4-4-4-4-4-");
    reSetDropDownModelDetailEventNewCar("truck");
  }
  //vjSon.success(function (arrData) {
  //    reSetCarModelData(arrData);
  //}).fail(function (ex) {
  //    alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //});
}
function reSetCarModelData(arrData) {
  $("#sbxSearchModel").html(""); // 초기화
  var innerHtml = "<option value=''>모델</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].ModelNo) {
      var vno = arrData[row].ModelNo;
      var vname = arrData[row].ModelName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  if (innerHtml.length == 0)
    innerHtml = "<option value='' selected>선택</option>";

  $("#sbxSearchModel").html(innerHtml);
  reSetCarModelEvent();
}
function reSetCarModelEvent() {
  // 데이터 등록 및 이벤트 등록
  $("#sbxSearchModel").selectbox("detach");
  $("#sbxSearchModel").selectbox({
    onChange: function (val, inst) {
      reLoadCarModelDetail(val);
      reLoadCarGrade("");
      reLoadCarGradeDetail("");
    },
  });
}

/* car modeldetail */
function reLoadCarModelDetail(model) {
  var vjSon = jSonDataModelDetail(model);
  reSetCarModelDetailData(vjSon);

  //vjSon.success(function (arrData) {
  //    reSetCarModelDetailData(arrData);
  //}).fail(function (ex) {
  //    alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //});
}
function reSetCarModelDetailData(arrData) {
  if ($("#sbxSearchModelDetail") != undefined) {
    $("#sbxSearchModelDetail").html(""); // 초기화
    var innerHtml = "<option value=''>세부모델</option>";
    for (var row = 0; row < arrData.length; row++) {
      if (arrData[row].MDetailNo) {
        var vno = arrData[row].MDetailNo;
        var vname = arrData[row].MDetailName;

        innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
      }
    }

    if (innerHtml.length == 0)
      innerHtml = "<option value='' selected>선택</option>";

    $("#sbxSearchModelDetail").html(innerHtml);
    reSetCarModelDetailEvent();
  }
}
function reSetCarModelDetailEvent() {
  // 데이터 등록 및 이벤트 등록
  $("#sbxSearchModelDetail").selectbox("detach");
  $("#sbxSearchModelDetail").selectbox({
    onChange: function (val, inst) {
      reLoadCarGrade(val);
      reLoadCarGradeDetail("");
    },
  });
}

/* car grade */
function reLoadCarGrade(modeldetail) {
  var vjSon = jSonDataGrade(modeldetail);
  reSetCarGradeData(vjSon);

  //vjSon.success(function (arrData) {
  //    reSetCarGradeData(arrData);
  //}).fail(function (ex) {
  //    alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //});
}
function reSetCarGradeData(arrData) {
  if ($("#sbxSearchGrade") != undefined) {
    $("#sbxSearchGrade").html(""); // 초기화
    var innerHtml = "<option value=''>등급</option>";
    for (var row = 0; row < arrData.length; row++) {
      if (arrData[row].GradeNo) {
        var vno = arrData[row].GradeNo;
        var vname = arrData[row].GradeName;

        innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
      }
    }

    if (innerHtml.length == 0)
      innerHtml = "<option value='' selected>선택</option>";

    $("#sbxSearchGrade").html(innerHtml).selectbox("detach");
    reSetCarGradeEvent();
  }
}
function reSetCarGradeEvent() {
  // 데이터 등록 및 이벤트 등록
  $("#sbxSearchGrade").selectbox({
    onChange: function (val, inst) {
      //console.log("val::", val);
      reLoadCarGradeDetail(val);
    },
  });
}

/* car gradedetail */
function reLoadCarGradeDetail(grade) {
  //console.log("abccccc", grade);
  var vjSon = jSonDataGradeDetail(grade);
  //  if (vjSon != null) {
  reSetCarGradeDetailData(vjSon);
  // } else {
  //alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //}

  //vjSon.success(function (arrData) {
  //    reSetCarGradeDetailData(arrData);
  //}).fail(function (ex) {
  //    alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //});
}
function reSetCarGradeDetailData(arrData) {
  if ($("#sbxSearchGradeDetail") != undefined) {
    $("#sbxSearchGradeDetail").html(""); // 초기화
    var innerHtml = "<option value=''>세부등급</option>";
    for (var row = 0; row < arrData.length; row++) {
      if (arrData[row].GDetailNo) {
        var vno = arrData[row].GDetailNo;
        var vname = arrData[row].GDetailName;

        innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
      }
    }

    if (innerHtml.length == 0)
      innerHtml = "<option valeu='' selected>선택</option>";

    // 데이터 등록 및 이벤트 등록
    $("#sbxSearchGradeDetail").html(innerHtml).selectbox("detach").selectbox();
    // 마지막은 이벤트를 등록 하지 않아도 된다. Search 일 경우 데이터를 담아야 하기 때문에 change 이벤트를 등록 한다.
  }
}

/* check info */
function ischeckRegDayBetweenDate() {
  var vSRegYear = $("#cbxSearchMakeSYear").val();
  if (vSRegYear == "") {
    vSRegYear = "0000";
  }
  var vSRegMonth = $("#cbxSearchMakeSDay").val();
  if (vSRegMonth == "") {
    vSRegMonth = "00";
  }
  var vERegYear = $("#cbxSearchMakeEYear").val();
  if (vERegYear == "") {
    vERegYear = "0000";
  }
  var vERegMonth = $("#cbxSearchMakeEDay").val();
  if (vERegMonth == "") {
    vERegMonth = "00";
  }
  var iSRegDay = 0;
  var iERegDay = 0;

  if (vSRegYear.length > 0 && vSRegMonth.length > 0) {
    iSRegDay = parseInt(vSRegYear) * 12 + parseInt(vSRegMonth);
  }
  if (vERegYear.length > 0 && vERegMonth.length > 0) {
    iERegDay = parseInt(vERegYear) * 12 + parseInt(vERegMonth);
  }
  if (!ischeckBetweenDate(iSRegDay, iERegDay)) {
    alert("시작일이 종료일보다 클 수 없습니다. 다시 선택하세요!");
    return false;
  }
  return true;
}
function ischeckUseKmBetweenNumber() {
  var vSDriveKm = $("#cbxSearchDriveS").val();
  var vEDriveKm = $("#cbxSearchDriveE").val();
  var iSDriveKm = 0;
  var iEDriveKm = 0;

  if (vSDriveKm != null && vSDriveKm.length > 0) {
    iSDriveKm = parseInt(vSDriveKm);
  }
  if (vEDriveKm != null && vEDriveKm.length > 0) {
    iEDriveKm = parseInt(vEDriveKm);
  }

  if (!ischeckBetweenDate(iSDriveKm, iEDriveKm)) {
    alert("검색에서 주행거리 범위를 잘못 선택하였습니다.");
    return false;
  }
  return true;
}
function ischeckCarAmountBetweenNumber() {
  var vSCarAmount = $("#cbxSearchMoneyS").val();
  var vECarAmount = $("#cbxSearchMoneyE").val();
  var iSCarAmount = 0;
  var iECarAmount = 0;

  if (vSCarAmount != null && vSCarAmount.length > 0) {
    iSCarAmount = parseInt(vSCarAmount);
  }
  if (vECarAmount != null && vECarAmount.length > 0) {
    iECarAmount = parseInt(vECarAmount);
  }

  if (!ischeckBetweenDate(iSCarAmount, iECarAmount)) {
    $("#cbxSearchMoneyS").val("");
    alert("검색에서 차량가격 범위를 잘못 선택하였습니다.");
    return false;
  }
  return true;
}
function ischeckSalingBetweenDate() {
  var vSSaleYear = $("#cbxSearchSSaleYear").val();
  var vSSaleMonth = $("#cbxSearchSSaleMonth").val();
  var vESaleYear = $("#cbxSearchESaleYear").val();
  var vESaleMonth = $("#cbxSearchESaleMonth").val();
  var iSSaleDay = 0;
  var iESaleDay = 0;

  if (vSSaleYear == "") {
    vSSaleYear = "0000";
  }
  if (vSSaleMonth == "") {
    vSSaleMonth = "00";
  }
  if (vESaleYear == "") {
    vESaleYear = "0000";
  }
  if (vESaleMonth == "") {
    vESaleMonth = "00";
  }

  if (vSSaleYear.length > 0 && vSSaleMonth.length > 0) {
    iSSaleDay = parseInt(vSSaleYear) * 12 + parseInt(vSSaleMonth);
  }
  if (vESaleYear.length > 0 && vESaleMonth.length > 0) {
    iESaleDay = parseInt(vESaleYear) * 12 + parseInt(vESaleMonth);
  }

  if (!ischeckBetweenDate(iSSaleDay, iESaleDay)) {
    alert("시작일이 종료일보다 클 수 없습니다. 다시 선택하세요!");
    return false;
  }
  return true;
}
function ischeckCarRegBetweenDate() {
  var vSRegYear = $("#cbxSearchSRegDayYear").val();
  var vSRegMonth = $("#cbxSearchSRegDayMonth").val();
  var vERegYear = $("#cbxSearchERegDayYear").val();
  var vERegMonth = $("#cbxSearchERegDayMonth").val();
  var iSRegDay = 0;
  var iERegDay = 0;

  if (vSRegYear.length > 0) {
    iSRegDay = parseInt(vSRegYear) * 12;
    if (vSRegMonth.length > 0) {
      iSRegDay = iSRegDay + parseInt(vSRegMonth);
    }
  }

  if (vERegYear.length > 0) {
    iERegDay = parseInt(vERegYear) * 12;
    if (vERegMonth.length > 0) {
      iERegDay = iERegDay + parseInt(vERegMonth);
    }
  }
  if (!ischeckBetweenDate(iSRegDay, iERegDay)) {
    alert(
      "차량등록일 검색에서 시작일이 종료일 보다 이후일 수는 없습니다. 다시 선택하세요!",
    );
    return false;
  }
  return true;
}
function ischeckCarADBetweenDate() {
  var vADSDays = $("#cbxSearchADStartDays").val();
  var vADEDays = $("#cbxSearchADEndDays").val();

  if (vADSDays.length > 0) {
    vADSDays = parseInt(vADSDays);
  }
  if (vADEDays.length > 0) {
    vADEDays = parseInt(vADEDays);
  }
  if (!ischeckBetweenDate(vADSDays, vADEDays)) {
    alert(
      "차량 광고기간 검색에서 시작일수가 종료일수 보다 이후일 수는 없습니다. 다시 선택하세요!",
    );
    return false;
  }
  return true;
}
function ischeckBetweenDate(iSSaleDay, iESaleDay) {
  if (iSSaleDay != 0 && iESaleDay != 0) {
    if (iSSaleDay > iESaleDay) {
      return false;
    }
  }
  return true;
}
function ischeckBetweenTruckTon() {
  var iSTon = $("#sbxCarTruckTonS").val();
  var iETon = $("#sbxCarTruckTonE").val();

  if (iSTon != "" && iETon != "") {
    if (parseFloat(iSTon) > parseFloat(iETon)) {
      alert("시작 화물톤이 종료 화물톤보다 클 수 없습니다. 다시 선택하세요!");
      return false;
    }
  }
  return true;
}

/*************************************************************/
/* 추후 공용화 함수로 만들기 */
/*************************************************************/
function reLoadJsonMaker(countryno) {
  // 데이터 등록
  reSetDropDownMakerList(Bizjs.GetMakerBase(countryno));
  // 스크릴 이벤트 생성
  reSetDropDownMakerEvent();

  //var Url = "/CarBase/JsonBaseCarMaker";

  //if (countryno != "") {
  //    var Url = "/CarBase/JsonBaseCarMaker/" + countryno;
  //}

  //$.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: Url,
  //    dataType: "json",
  //    success: function (data) {
  //        // 데이터 등록
  //        reSetDropDownMakerList(data);
  //        // 스크릴 이벤트 생성
  //        reSetDropDownMakerEvent();
  //    },
  //    fail: function (data) {
  //        alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //    }
  //});
}
function reLoadJsonModel(makerno) {
  // 데이터 등록
  //중대형화물
  if (makerno != "10061") {
    //console.log("1111");
    reSetDropDownModelList(Bizjs.GetModelBase(makerno));
  } else {
    //console.log("2222");
    reSetDropDownModelListTruckS();
    reLoadModelDetailTruckS();
    reSetDropDownModelDetailEvent("truck");
  }
  // 스크롤 이벤트 생성
  reSetDropDownModelEvent();

  //var Url = "/CarBase/JsonBaseCarModel/" + makerno;

  //$.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: Url,
  //    dataType: "json",
  //    success: function (data) {
  //        // 데이터 등록
  //        reSetDropDownModelList(data);
  //        // 스크롤 이벤트 생성
  //        reSetDropDownModelEvent();
  //    },reSetDropDownModelEvent
  //    fail: function (data) {
  //        alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //    }
  //});
}
function reLoadJsonModelDetail(modelno) {
  //console.log("reLoadJsonModelDetail");
  // 설정 초기화
  reSetSearchModelDetail();
  // 데이터 등록
  reSetDropDownModelDetailList(Bizjs.GetModelDetailBase(modelno));
  // 스크롤 이벤트 생성
  reSetDropDownModelDetailEvent();

  //var Url = "/CarBase/JsonBaseCarModelDetail/" + modelno;
  //$.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: Url,
  //    dataType: "json",
  //    success: function (data) {
  //        // 데이터 등록
  //        reSetDropDownModelDetailList(data);
  //        // 스크롤 이벤트 생성
  //        reSetDropDownModelDetailEvent();
  //    },
  //    fail: function (data) {
  //        alert("세부 모델 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //    }
  //});
}
function reLoadJsonGrade(modeldetailno) {
  // 데이터 등록
  reSetDropDownGradeList(Bizjs.GetGradeBase(modeldetailno));
  // 스크릴 이벤트 생성
  reSetDropDownGradeEvent();

  //var Url = "/CarBase/JsonBaseCarGrade/" + modeldetailno;
  //$.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: Url,
  //    dataType: "json",
  //    success: function (data) {
  //        // 데이터 등록
  //        reSetDropDownGradeList(data);
  //        // 스크릴 이벤트 생성
  //        reSetDropDownGradeEvent();
  //    },
  //    fail: function (data) {
  //        alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //    }
  //});
}
function reLoadJsonGradeDetail(gradeno) {
  // 데이터 등록
  reSetDropDownGradeDetailList(Bizjs.GetGradeDetailBase(gradeno));
  // 스크릴 이벤트 생성
  reSetDropDownGradeDetailEvent();

  //var Url = "/CarBase/JsonBaseCarGradeDetail/" + gradeno;
  //$.ajax({
  //    type: 'POST',
  //    cache: false,
  //    contentType: "application/json; charset=utf-8",
  //    url: Url,
  //    dataType: "json",
  //    success: function (data) {
  //        // 데이터 등록
  //        reSetDropDownGradeDetailList(data);
  //        // 스크릴 이벤트 생성
  //        reSetDropDownGradeDetailEvent();
  //    },
  //    fail: function (data) {
  //        alert("제조사 데이터 로드에 오류가 발생하였습니다. 계속 될 경우 관리자에게 문의하세요.");
  //    }
  //});
}

/* 관련 데이터 리스트 */
// 제조사 데이터 리스트 화
function reSetDropDownCountryEvent() {
  $("#cbxSearchCountry").selectbox("detach");
  $("#cbxSearchCountry").selectbox({
    onChange: function (val, inst) {
      reLoadJsonMaker(val);
      reSetDropDownModelClear();
    },
    classHolder: "sbHolderS",
    classHolderDisabled: "sbHolderDisabledS",
    classSelector: "sbSelectorS",
    classOptions: "sbOptionsS",
    classGroup: "sbGroupS",
    classSub: "sbSubS",
    classDisabled: "sbDisabledS",
    classToggleOpen: "sbToggleOpenS",
    classToggle: "sbToggleS",
    classFocus: "sbFocusS",
  });
  $("#cbxSearchCountry").selectbox("attach");
}
function reSetDropDownMakerList(arrData) {
  $("#cbxSearchMaker").html(""); // 초기화
  var innerHtml = "<option value=''>제조사선택</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].MakerNo) {
      var vno = arrData[row].MakerNo;
      var vname = arrData[row].MakerName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }
  $("#cbxSearchMaker").html(innerHtml);
}
// 모델 데이터 리스트 화
function reSetDropDownModelList(arrData) {
  $("#cbxSearchModel").html(""); // 초기화
  var innerHtml = "<option value=''>모델선택</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].ModelNo) {
      var vno = arrData[row].ModelNo;
      var vname = arrData[row].ModelName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  $("#cbxSearchModel").html(innerHtml);
}
//트럭모델..
function reSetDropDownModelListTruckS() {
  //console.log("3333");
  $("#cbxSearchModel").html(""); // 초기화
  var innerHtml = "<option value=''>세부모델선택시 자동선택</option>";
  $("#cbxSearchModel").html(innerHtml);
}
function reLoadModelDetailTruckS(modelDetail, compcall) {
  //console.log("44444");
  //reSetSearchModelDetail();
  reSetSearchModelDetailListTruck(
    Bizjs.GetModelDetailBaseTruck("truck"),
    modelDetail,
  );
}
//트럭모델 신차..
function reSetDropDownModelListTruckSNewCar() {
  $("#sbxSearchModel").html(""); // 초기화
  var innerHtml = "<option value=''>세부모델선택시 자동선택</option>";
  $("#sbxSearchModel").html(innerHtml);
  $("#sbxSearchModel").selectbox("detach");
  $("#sbxSearchModel").selectbox("attach");
}
function reLoadModelDetailTruckSNewCar(modelDetail, compcall) {
  //console.log("44444cccddd");
  reSetSearchModelDetailListTruckNewCar(
    Bizjs.GetModelDetailBaseTruck("truck"),
    modelDetail,
  );
}
// 모델 상세 데이터 화면등록
function reSetDropDownModelDetailList(arrData) {
  $("#cbxSearchModelDetail").html(""); // 초기화
  var innerHtml = "<option value=''>세부모델 전체</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].MDetailNo) {
      var vno = arrData[row].MDetailNo;
      var vname = arrData[row].MDetailName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  $("#cbxSearchModelDetail").html(innerHtml);
}
// 모델 상세 데이터 화면등록 - 트럭
function reSetSearchModelDetailListTruck(arrData, modelDetail) {
  //console.log("55555");
  //console.log("modelDetail", arrData);
  $("#cbxSearchModelDetail").html(""); // 초기화
  var innerHtml = "<option value=''>세부모델 전체</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].MDetailNo) {
      var vno = arrData[row].MDetailNo;
      var vname = arrData[row].MDetailName;
      var modelNo = arrData[row].ModelNo;
      if (modelDetail && modelDetail == vno) {
        innerHtml +=
          "<option value='" + vno + "' selected>" + vname + "</option>\r\n";
      }
      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }
  if (innerHtml.length == 0)
    innerHtml = "<li>등록된 세부모델정보가 없습니다.</li>";

  //console.log(innerHtml);
  $("#cbxSearchModelDetail").html(innerHtml);
  $("#cbxSearchModelDetail").selectbox("detach");
  $("#cbxSearchModelDetail").selectbox("attach");
}
//모델 상세 데이터 화면등록 - 트럭 신차
function reSetSearchModelDetailListTruckNewCar(arrData, modelDetail) {
  //console.log("reSetSearchModelDetailListTruckNewCar::::", modelDetail);
  $("#sbxSearchModelDetail").html(""); // 초기화
  var innerHtml = "<option value=''>세부모델</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].MDetailNo) {
      var vno = arrData[row].MDetailNo;
      var vname = arrData[row].MDetailName;
      var modelNo = arrData[row].ModelNo;
      if (modelDetail && modelDetail == vno) {
        innerHtml +=
          "<option value='" + vno + "' selected>" + vname + "</option>\r\n";
      }
      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }
  //if (innerHtml.length == 0)
  //    innerHtml = "<option>등록된 세부모델정보가 없습니다.</option>";

  //console.log(innerHtml);
  //console.log("innerHtmllllllll");
  $("#sbxSearchModelDetail").html(innerHtml);
  $("#sbxSearchModelDetail").selectbox("detach");
  $("#sbxSearchModelDetail").selectbox("attach");
}
// 등급 데이터 화면 등록
function reSetDropDownGradeList(arrData) {
  $("#cbxSearchGrade").html(""); // 초기화
  var innerHtml = "<option value=''>등급 전체</option>";
  //if(arrData.index)
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].GradeNo) {
      var vno = arrData[row].GradeNo;
      var vname = arrData[row].GradeName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  $("#cbxSearchGrade").html(innerHtml);
}
// 등급 데이터 화면 등록
function reSetDropDownGradeDetailList(arrData) {
  $("#cbxSearchGradeDetail").html(""); // 초기화
  var innerHtml = "<option value=''>세부등급 전체</option>";
  for (var row = 0; row < arrData.length; row++) {
    if (arrData[row].GDetailNo) {
      var vno = arrData[row].GDetailNo;
      var vname = arrData[row].GDetailName;

      innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
    }
  }

  $("#cbxSearchGradeDetail").html(innerHtml);
}

/* 관련 이벤트 리스트 */
// 국사 클릭 이벤트 -- 기본등록으로 설정한다.
function reSetDropDownCountryEvent() {
  $("#cbxSearchCountry").selectbox("detach");
  $("#cbxSearchCountry").selectbox({
    onChange: function (val, inst) {
      reLoadJsonMaker(val);
      reSetDropDownModelClear();
    },
    classHolder: "sbHolderS",
    classHolderDisabled: "sbHolderDisabledS",
    classSelector: "sbSelectorS",
    classOptions: "sbOptionsS",
    classGroup: "sbGroupS",
    classSub: "sbSubS",
    classDisabled: "sbDisabledS",
    classToggleOpen: "sbToggleOpenS",
    classToggle: "sbToggleS",
    classFocus: "sbFocusS",
  });
  $("#cbxSearchCountry").selectbox("attach");
}
// 제조사 데이터 클릭 이벤트
function reSetDropDownMakerEvent() {
  $("#cbxSearchMaker")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        //console.log("666666");
        //중대형화물 = 10061
        if (val == "10061") {
          //console.log("여ㅓ기구나");
          reLoadJsonModel(val);
          //reLoadModelDetailTruckS();
        } else {
          //console.log("77777");
          //console.log("여ㅓ기구나2222");
          reLoadJsonModel(val);
          reSetDropDownModelDetailClear();
        }

        //reLoadJsonModel(val);
        //reSetDropDownModelDetailClear();
      },
      classHolder: "sbHolderS",
      classHolderDisabled: "sbHolderDisabledS",
      classSelector: "sbSelectorS",
      classOptions: "sbOptionsS",
      classGroup: "sbGroupS",
      classSub: "sbSubS",
      classDisabled: "sbDisabledS",
      classToggleOpen: "sbToggleOpenS",
      classToggle: "sbToggleS",
      classFocus: "sbFocusS",
    });
}
// 모델 데이터 클릭 이벤트
function reSetDropDownModelEvent() {
  $("#cbxSearchModel")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        reLoadJsonModelDetail(val);
        reSetDropDownGradeClear();
      },
      classHolder: "sbHolderS",
      classHolderDisabled: "sbHolderDisabledS",
      classSelector: "sbSelectorS",
      classOptions: "sbOptionsS",
      classGroup: "sbGroupS",
      classSub: "sbSubS",
      classDisabled: "sbDisabledS",
      classToggleOpen: "sbToggleOpenS",
      classToggle: "sbToggleS",
      classFocus: "sbFocusS",
    });
}
// 모델 상세 데이터 클릭 이벤트
function reSetDropDownModelDetailEvent(compcall) {
  //console.log("reSetDropDownModelDetailEvent123");
  $("#cbxSearchModelDetail")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        if (
          compcall == "truck" ||
          $("#tbxSearchMaker  option:selected").val() == "10061"
        ) {
          GetTruckModelMapping(val);
        }
        //console.log("val : ", val);
        reLoadJsonGrade(val);
        reSetDropDownGradeDetailClear();
      },
      classHolder: "sbHolderS",
      classHolderDisabled: "sbHolderDisabledS",
      classSelector: "sbSelectorS",
      classOptions: "sbOptionsS",
      classGroup: "sbGroupS",
      classSub: "sbSubS",
      classDisabled: "sbDisabledS",
      classToggleOpen: "sbToggleOpenS",
      classToggle: "sbToggleS",
      classFocus: "sbFocusS",
    });
}
// 모델 상세 데이터 클릭 이벤트
function reSetDropDownModelDetailEventNewCar(compcall) {
  //console.log("reSetDropDownModelDetailEvent12333333");
  $("#sbxSearchModelDetail")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        if (
          compcall == "truck" ||
          $("#sbxSearchMaker  option:selected").val() == "10061"
        ) {
          GetTruckModelMappingNewCar(val);
        }
        //console.log("val : ", val);
        //reLoadJsonGrade(val);
        //reSetDropDownGradeDetailClear();
      },
      classHolder: "sbHolderS",
      classHolderDisabled: "sbHolderDisabledS",
      classSelector: "sbSelectorS",
      classOptions: "sbOptionsS",
      classGroup: "sbGroupS",
      classSub: "sbSubS",
      classDisabled: "sbDisabledS",
      classToggleOpen: "sbToggleOpenS",
      classToggle: "sbToggleS",
      classFocus: "sbFocusS",
    });
}
//트럭코드 세부모델선택시 모델가져오기
function GetTruckModelMapping(modeldetailNo) {
  //console.log("888888", modeldetailNo);
  if ($("#cbxSearchMaker").val() == "10061") {
    var selectModelDetail = "";
    if (!modeldetailNo) {
      selectModelDetail = $("#cbxSearchModelDetail  option:selected").val();
    } else {
      selectModelDetail = modeldetailNo;
    }
    //console.log("aaad", selectModelDetail);
    if (selectModelDetail) {
      //console.log(_CheckTruckCode);
      //트럭코드 디테일먼저 가져오기
      var mDetailNo = "";
      var mDetailModelNo = "";
      $.each(_CheckTruckCode, function (key, value) {
        if (value.MDetailNo === selectModelDetail) {
          mDetailModelNo = value.ModelNo;
          return false;
        }
      });

      var modelName = "";
      //트럭코드 모델 가져오기
      var modelArr = CarBaseModel[10061];
      var modelName = "";
      var modelVal = "";

      $.each(modelArr, function (key, value) {
        if (value.ModelNo === mDetailModelNo) {
          modelName = value.ModelName;
          modelVal = value.ModelNo;
          return false;
        }
      });

      var innerHtml =
        "<option value='" + modelVal + "'>" + modelName + "</option>\r\n";

      $("#cbxSearchModel").html(""); // 초기화
      $("#cbxSearchModel").selectbox("detach");
      $("#cbxSearchModel").html(innerHtml);
      $("#cbxSearchModel").selectbox();
    }
  }
}
function GetTruckModelMappingNewCar(modeldetailNo) {
  //console.log("GetTruckModelMappingNewCaraaaa");
  if ($("#sbxSearchMaker").val() == "10061") {
    var selectModelDetail = "";
    if (!modeldetailNo) {
      selectModelDetail = $("#sbxSearchModelDetail  option:selected").val();
    } else {
      selectModelDetail = modeldetailNo;
    }
    //console.log("aaad", selectModelDetail);
    if (selectModelDetail) {
      //console.log(_CheckTruckCode);
      //트럭코드 디테일먼저 가져오기
      var mDetailNo = "";
      var mDetailModelNo = "";
      $.each(_CheckTruckCode, function (key, value) {
        if (value.MDetailNo === selectModelDetail) {
          mDetailModelNo = value.ModelNo;
          return false;
        }
      });

      var modelName = "";
      //트럭코드 모델 가져오기
      var modelArr = CarBaseModel[10061];
      var modelName = "";
      var modelVal = "";

      $.each(modelArr, function (key, value) {
        if (value.ModelNo === mDetailModelNo) {
          modelName = value.ModelName;
          modelVal = value.ModelNo;
          return false;
        }
      });

      var innerHtml =
        "<option value='" + modelVal + "'>" + modelName + "</option>\r\n";

      $("#sbxSearchModel").html(""); // 초기화
      $("#sbxSearchModel").selectbox("detach");
      $("#sbxSearchModel").html(innerHtml);
      $("#sbxSearchModel").selectbox();
    }
  }
}
// 등급 데이터 크릭 이벤트
function reSetDropDownGradeEvent() {
  $("#cbxSearchGrade")
    .selectbox("detach")
    .selectbox({
      onChange: function (val, inst) {
        reLoadJsonGradeDetail(val);
      },
      classHolder: "sbHolderS",
      classHolderDisabled: "sbHolderDisabledS",
      classSelector: "sbSelectorS",
      classOptions: "sbOptionsS",
      classGroup: "sbGroupS",
      classSub: "sbSubS",
      classDisabled: "sbDisabledS",
      classToggleOpen: "sbToggleOpenS",
      classToggle: "sbToggleS",
      classFocus: "sbFocusS",
    });
}
// 등급 데이터 크릭 이벤트
function reSetDropDownGradeDetailEvent() {
  $("#cbxSearchGradeDetail").selectbox("detach").selectbox({
    classHolder: "sbHolderS",
    classHolderDisabled: "sbHolderDisabledS",
    classSelector: "sbSelectorS",
    classOptions: "sbOptionsS",
    classGroup: "sbGroupS",
    classSub: "sbSubS",
    classDisabled: "sbDisabledS",
    classToggleOpen: "sbToggleOpenS",
    classToggle: "sbToggleS",
    classFocus: "sbFocusS",
  });
}

/* 초기화 */
function reSetDropDownMakerClear() {
  $("#cbxSearchMaker").html("<option value=''>제조사선택</option>"); // 초기화
  reSetDropDownMakerEvent();
  reSetDropDownModelClear();
}
function reSetDropDownModelClear() {
  $("#cbxSearchModel").html("<option value=''>모델선택</option>"); // 초기화
  reSetDropDownModelEvent();
  reSetDropDownModelDetailClear();
}
function reSetDropDownModelDetailClear() {
  $("#cbxSearchModelDetail").html("<option value=''>세부모델 전체</option>"); // 초기화
  reSetDropDownModelDetailEvent();
  reSetDropDownGradeClear();
}
function reSetDropDownGradeClear() {
  $("#cbxSearchGrade").html("<option value=''>등급 전체</option>"); // 초기화
  reSetDropDownGradeEvent();
  reSetDropDownGradeDetailClear();
}
function reSetDropDownGradeDetailClear() {
  $("#cbxSearchGradeDetail").html("<option value=''>세부등급 전체</option>"); // 초기화
  reSetDropDownGradeDetailEvent();
}
