/**************************************** 이전비용 탭 START ********************************************************/
/*과세시가구분 라디오 버튼*/
function reLoadMoveRegistAssess(carno) {
  $("#ui_mrregiamount").html("");
  $("#ui_mrnumberchangeamount").html("");
  $("#ui_mrtakeamount").html("");
  $("#ui_mrstampamount").html("");
  $("#ui_mragentcost").html("");
  $("#ui_mrbondamount").html("");
  $("#ui_mrtotalamount").html("");

  $("#hdfCarAmountMD").val("");
  if (carno == null) {
    $("#ui_carmoveregist").hide();
    $("#ui_carmoveregisttext").show();
    $("#ui_cartranscost").show();
  } else {
    // 차량 정보가 있음으로 데이터를 가지고 온다.
    reLoadMoveRegistCar(carno);
    $("#ui_carmoveregist").show();
    $("#ui_carmoveregisttext").hide();
    $("#ui_cartranscost").hide();
  }
}

function reLoadMoveRegistCar(carno) {
  var Url = "/CarBase/JsonBaseCarMoveRegistAssess";
  $.ajax({
    type: "POST",
    cache: false,
    contentType: "application/json; charset=utf-8",
    url: Url,
    data: JSON.stringify({
      carno: carno,
    }),
    dataType: "json",
    success: function (arrData) {
      var innerHtml =
        "<option value='' selected>과세표준에 등록된 차량을 선택해주세요! (신차가격)</option>";
      for (var row = 0; row < arrData.length; row++) {
        if (arrData[row].MRNo) {
          var vno = arrData[row].MRNo;
          var vname =
            arrData[row].MRName + " [ 가격 : " + arrData[row].MRPrice + " ]";
          innerHtml += "<option value='" + vno + "'>" + vname + "</option>\r\n";
        }
      }
      $("#sbxCarMoveRegist").selectbox("detach");
      $("#sbxCarMoveRegist").html(innerHtml);
      $("#sbxCarMoveRegist").selectbox("attach").selectbox("open");
    },
    fail: function (data) {
      alert(data);
    },
  });
}
/* 이전비 인쇄 */
function goPrintTranAmount() {
  var vCarAmount = $("#ui_ViewCarAmount").html();
  var vCarTotalAmount = $("#ui_mrtotalamount").html();
  if (
    vCarAmount == "" ||
    vCarAmount == "0" ||
    vCarTotalAmount == "" ||
    vCarTotalAmount == "0"
  ) {
    alert("계산하기를 진행한 후 내역을 인쇄 하실 수 있습니다.");
    return;
  }

  if (confirm("이전비용을 인쇄하시겠습니까?")) {
    // 파라미터를 생성 URL 을 생성 합니다.
    var urlPara = {
      CarAmount: vCarAmount,
      CarName: $("#ui_ViewCarName").html(),
      CarRegDay: $("#ui_ViewCarReg").html(),
      CarRegYear: $("#ui_ViewCarRegYear").html(),
      CarApplyDay: $("#hdfCarApplyDay").val(),
      CarAmountMD: $("#hdfCarAmountMD").val(),
      CarRegiAmount: $("#ui_mrregiamount").html(),
      CarNumberChangeAmount: $("#ui_mrnumberchangeamount").html(),
      CarTakeAmount: $("#ui_mrtakeamount").html(),
      CarStampAmount: $("#ui_mrstampamount").html(),
      CarAgentAmount: $("#ui_mragentcost").html(),
      CarBondAmount: $("#ui_mrbondamount").html(),
      CarTotalAmount: vCarTotalAmount,
    };

    var url = $.param(urlPara);
    parent.SetPrintPageCarTransCost(url);
  }
}

/* 과세표준액 (계산하기 버튼 클릭 이벤트 없음) */
function setMoveRegisterCar() {
  var vMr = $("#sbxCarMoveRegist").val();
  if (vMr.length > 0) {
    $("#ui_cartranscost").show();
  } else {
    $("#ui_cartranscost").hide();
  }
}

/* 이전비 계산 */
function goCalculate(carno, vCarDetailNo) {
  var vCarAmount = $(':radio[name="rdoCarAmount"]:checked').val();
  var vCarMoveRegist = $("#sbxCarMoveRegist").val();
  if (vCarAmount == "0") {
    if (vCarMoveRegist == "") {
      alert("과세표준에 등록된 차량을 선택하세요!");
      return;
    }
  } else {
    vCarMoveRegist = "0";
    if (vCarDetailNo.length == 0) {
      alert(
        "차량등급이 설정되지 않아 판매금액으로 이전비용을 계산할 수없습니다.",
      );
      return;
    }
  }
  var vCarUseGubun = $(':radio[name="rdoCarUseGubun"]:checked').val();
  var vMetroArea = $(':radio[name="rdoMetroArea"]:checked').val();
  var vCarNumberChange = $(':radio[name="rdoCarNumberChange"]:checked').val();
  var vCarNumberSub = $(':radio[name="rdoCarNumberSub"]:checked').val();
  var vPublicOfficeStamp = $(
    ':radio[name="rdoPublicOfficeStamp"]:checked',
  ).val();
  var vBondPurchasePer = $(':radio[name="rdoBondPurchasePer"]:checked').val();
  var vCarRegistProxyAmount = $("#sbxRegistProxyAmount").val();

  var dataPara = {
    para: {
      CarBondmode: vCarAmount,
      CarNo: carno,
      CarPosArea: vMetroArea,
      CarUseGubun: vCarUseGubun,
      CarPublicPer: vBondPurchasePer,
      CarMoveRegistNo: vCarMoveRegist,
    },
  };

  var Url = "/CarBase/JsonBaseCarMoveRegist";
  $.ajax({
    type: "POST",
    cache: false,
    contentType: "application/json; charset=utf-8",
    url: Url,
    data: JSON.stringify(dataPara),
    dataType: "json",
    success: function (arrData) {
      if (arrData) {
        if (arrData.CarStandAmt) {
          // 숫자형으로 변환
          var iCarNumberChange = $.isNumeric(vCarNumberChange)
            ? parseInt(vCarNumberChange)
            : 0;
          var iCarNumberSub = $.isNumeric(vCarNumberSub)
            ? parseInt(vCarNumberSub)
            : 0;
          var iPublicOfficeStamp = $.isNumeric(vPublicOfficeStamp)
            ? parseInt(vPublicOfficeStamp)
            : 0;
          var iCarRegistProxyAmount = $.isNumeric(vCarRegistProxyAmount)
            ? parseInt(vCarRegistProxyAmount)
            : 0;
          var iCarRegiAmt = $.isNumeric(arrData.CarRegiAmt)
            ? parseInt(arrData.CarRegiAmt)
            : 0;
          var iCarTakeAmt = $.isNumeric(arrData.CarTakeAmt)
            ? parseInt(arrData.CarTakeAmt)
            : 0;
          var iCarPublicAmt = $.isNumeric(arrData.CarPublicAmtCalc)
            ? parseInt(arrData.CarPublicAmtCalc)
            : 0;

          var vCarAmount =
            $(':radio[name="rdoCarAmount"]:checked').val() == "0"
              ? "과세표준액"
              : "판매금액";
          $("#hdfCarAmountMD").val(vCarAmount);
          $("#ui_mrregiamount").html($.number(iCarRegiAmt));
          $("#ui_mrnumberchangeamount").html(
            $.number(iCarNumberChange + iCarNumberSub),
          );
          $("#ui_mrtakeamount").html($.number(iCarTakeAmt));
          $("#ui_mrstampamount").html($.number(iPublicOfficeStamp));
          $("#ui_mragentcost").html($.number(iCarRegistProxyAmount));
          $("#ui_mrbondamount").html($.number(iCarPublicAmt));

          var iCarTotalAmount =
            iCarRegiAmt +
            iCarNumberChange +
            iCarNumberSub +
            iCarTakeAmt +
            iPublicOfficeStamp +
            iCarRegistProxyAmount +
            iCarPublicAmt;
          $("#ui_mrtotalamount").html($.number(iCarTotalAmount));
        }
      }
    },
    fail: function (data) {
      alert(data);
    },
  });
}
/**************************************** 이전비용 탭 END ********************************************************/

/**************************************** 성능인쇄 탭 START ********************************************************/
/*인쇄하기 */
function printCarCheckOut() {
  var browser = navigator.userAgent.toLowerCase();
  if (-1 != browser.indexOf("chrome")) {
    openPrintWindow();
  } else if (-1 != browser.indexOf("trident")) {
    openPrintWindow();
  }
}
/*인쇄하기 */
function goPrintPage() {
  window.open(
    carcheckoutUrl,
    "_blank",
    "height=" + screen.height + ",width=" + screen.width + "fullscreen=yes",
  );
}

function openPrintWindow() {
  if ($("#NewGubun").val() == "A") {
    var chkseq = $("#ChkSeq").val();
    var url =
      "http://www.autocafe.co.kr/asso/Check_Form_2020_2p.asp?Chkseq=" + chkseq;
    window.open(url);
    return;
  } else {
    var title = "카매니저";
    var openPopUp = window.open("", title, "status=no");
    var frmData = document.frmData;
    frmData.target = title;
    if ($("#NewGubun").val() == "Y") {
      //2018버전
      frmData.action = "/print/PrintCarCheckOut_New";
    } else {
      //2016버전
      frmData.action = "/print/PrintCarCheckOut";
    }
    frmData.submit();

    setTimeout(function () {
      if (!openPopUp || openPopUp.closed) {
        vLoading.hide();
      }
    }, 3000);
  }
}
/**************************************** 성능인쇄 탭 END ********************************************************/

/**************************************** 사진정보 탭 START ********************************************************/
/* 인쇄하기 */
function carDetailPrint(CarNo) {
  window.open("/print/printCarDetail/" + CarNo, "카매니저", "status=no");
}
/**************************************** 사진정보 탭 END ********************************************************/

/**************************************** 공통 START ********************************************************/
/* 탭이벤트 */
function reLoadPopupCarDetailTabEvent() {
  /* 탭컨트롤 */
  $("#content .nav li").each(function (index) {
    $(this).click(function () {
      $(".r_price").show(); // 가격정보 노출

      $("#carPrintBtn").hide(); // 상세페이지 버튼
      $("#carPrintBtn02").hide(); //자체 성능점검
      $("#carPrintBtn03").hide(); //외부 성능점검 URL

      $("#content .nav li").removeClass("onhover"); // 탭메뉴 색상 변경
      $(this).addClass("onhover"); // 탭메뉴 색상 변경

      $("#content .uc_tabview").hide(); // 탭메뉴 화면 노출
      $("#content .uc_tabview").eq(index).show(); // 탭메뉴 화면 노출

      if ($(this).hasClass("phototab")) {
        $("#carPrintBtn").show(); // 상세페이지 버튼
        leasecalCheck = false;
      } else if ($(this).hasClass("detailoptiontab")) {
        var infoh = $(".num01sub").height();
        $(".num01sub.c1, .num01sub.c2, .num01sub.c3").height(infoh);
        leasecalCheck = false;
      } else if ($(this).hasClass("checkouttab")) {
        if ($("#ChkSeq").val()) {
          $("#carPrintBtn02").show();
        } else if (carcheckoutUrl != null && carcheckoutUrl != "") {
          $("#carPrintBtn03").show();
        }

        if ($("#carcheckout").attr("src") === "" && carcheckoutUrl != "") {
          $("#carcheckout").attr(
            "src",
            encodeURI(carcheckoutUrl.replace("print=1", "print=0")),
          );
        }
        if ($("#carcheckout").attr("src") === "") {
          $("#carcheckout").attr(
            "src",
            "http://autocafe.co.kr/ASSO/CarCheck_Form.asp?OnCarNo=@mCarDetail.CarOnCarNo",
          );
        }
        if (
          !$("#ChkSeq").val() &&
          $("#ChkSeq").val() != "0" &&
          !$("#NewGubun").val()
        ) {
          carCheckOut.search();
        }
        leasecalCheck = false;
      } else if ($(this).hasClass("transfercosttab")) {
        reLoadMoveRegistAssess();
        leasecalCheck = false;
      } else if ($(this).hasClass("leasecalctab")) {
        $(".r_price").hide(); // 가격정보 미노출
        dgbLeaseLog(1); //페이지 호출 로그(1) 등록
        dgbsearch(1); // 데이터 노출
      }
    });
  });
}

/* 차량번호 "번호복사" 기능*/
function carPlateNumberCopy() {
  $("#carplatenoCopy").select();
  var successful = document.execCommand("copy");
}

function reLoadPopupCarImageEvent() {
  $("#photoPage1 a.img_box").each(function (index) {
    $(this).click(function () {
      $("#photoPage1 a").removeClass("on");
      var _$img = $(this).children("img").eq(1).clone();
      if (
        typeof typeof $(this).children("img").eq(1).attr("src") === "undefined"
      ) {
        $("#modelimg").html(
          "<img src='/include/image/car/car_noimage_big.jpg'/>",
        );
      } else {
        $("#modelimg").html(_$img.show());
      }
      wheelzoom($("#modelimg").find("img"));
      $(this).addClass("on");
    });

    $(this).hover(function () {
      $("#photoPage1 a").removeClass("on");
      var _$img = $(this).children("img").eq(1).clone();
      if (
        typeof typeof $(this).children("img").eq(1).attr("src") === "undefined"
      ) {
        $("#modelimg").html(
          "<img src='/include/image/car/car_noimage_big.jpg'/>",
        );
      } else {
        $("#modelimg").html(_$img.show());
      }
      wheelzoom($("#modelimg").find("img"), { maxZoom: 3 });
      $(this).addClass("on");
    });
  });
}

//사진정보 "이전","다음"이미지 노출 클릭 이벤트
function reLoadPopupThumbViewEvent() {
  var vIndex = 0;
  $(".thumb_view .prev").click(function () {
    var vThumbMaxCount =
      $("#hdfCarImageCount").val() == ""
        ? 0
        : Number($("#hdfCarImageCount").val());
    vIndex = vThumbIndex - 1 < 0 ? vThumbMaxCount - 1 : vThumbIndex - 1;
    $("#photoPage1 a").eq(vIndex).trigger("click");
    vThumbIndex = vIndex;
  });
  $(".thumb_view .next").click(function () {
    var vThumbMaxCount =
      $("#hdfCarImageCount").val() == ""
        ? 0
        : Number($("#hdfCarImageCount").val());
    vIndex = vThumbIndex + 1 >= vThumbMaxCount ? 0 : vThumbIndex + 1;
    $("#photoPage1 a").eq(vIndex).trigger("click");
    vThumbIndex = vIndex;
  });
}

/**************************************** 공통 END ********************************************************/
