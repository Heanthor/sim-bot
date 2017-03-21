/**
 * Created by reedt on 3/20/2017.
 */

$(function () {
    $("#submitguild").on('click', function () {
        console.log("Clicked");
        $.get(
            "all_sims/",
            {
                "region": $("#region").val(),
                "weeks": $("#weeks").val(),
                "difficulty": $("#difficulty").val(),
                "guild": $("#guildname").val(),
                "realm": $("#realm").val()
            },
            function (data) {
                $("#guild-report-printout").html(data);
            }
        );
    })
});
