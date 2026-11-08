(function ($) {
  var OPEN_EVENTS = {
    eligibility_notice: true,
    vote_invite: true,
  };
  var CLOSE_EVENTS = {
    voting_closing_reminder: true,
  };
  var STATUS_EVENTS = {
    voting_opened: true,
    voting_closed: true,
  };

  function modeFor(eventVal) {
    if (OPEN_EVENTS[eventVal]) return "open";
    if (CLOSE_EVENTS[eventVal]) return "close";
    if (STATUS_EVENTS[eventVal]) return "status";
    return null;
  }

  function timingField($scope) {
    return $scope
      .find(
        ".form-row.field-send_offset_minutes, .field-send_offset_minutes"
      )
      .first()
      .closest(".form-row, .fieldBox, .flex-container, .form-group, div");
  }

  function labelFor(mode) {
    if (mode === "open") {
      return {
        label: "Minutes before voting opens",
        help: "Send this email this many minutes before voting opens.",
      };
    }
    if (mode === "close") {
      return {
        label: "Minutes before voting closes",
        help: "Send this reminder this many minutes before voting closes (unsubmitted ballots only).",
      };
    }
    return null;
  }

  function syncRow($row) {
    var $sel = $row.find('select[name="event"], select[name$="-event"]').first();
    if (!$sel.length) return;
    var mode = modeFor($sel.val());
    var $timing = timingField($row);
    if (!$timing.length) return;

    var meta = labelFor(mode);
    if (mode === "status" || mode === null) {
      $timing.hide();
    } else {
      $timing.show();
      if (meta) {
        $timing.find("label").first().text(meta.label);
        var $help = $timing.find(".help, .helptext").first();
        if ($help.length) $help.text(meta.help);
      }
    }
  }

  function syncAll() {
    $("form").each(function () {
      var $form = $(this);
      if ($form.find('select[name="event"]').length) {
        syncRow($form);
      }
    });
    $(".inline-related").each(function () {
      syncRow($(this));
    });
  }

  $(function () {
    syncAll();
    $(document).on(
      "change",
      'select[name="event"], select[name$="-event"]',
      function () {
        syncRow($(this).closest(".inline-related, form"));
      }
    );
    $(document).on("formset:added", function (event, $row) {
      syncRow($row || $(event.target));
    });
  });
})(django.jQuery);
