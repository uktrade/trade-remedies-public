"use strict";
const path = require("path");
const gulp = require("gulp");
const sass = require("gulp-sass");
const sourcemaps = require("gulp-sourcemaps");
const del = require("del");

const PROJECT_DIR = path.resolve(__dirname);
const SASS_WATCH_FILES = `${PROJECT_DIR}/trade_remedies_public/templates/sass/**/*.scss`;
const SASS_MAIN = `${PROJECT_DIR}/trade_remedies_public/templates/sass/*.scss`;
const STATIC_DIR = `${PROJECT_DIR}/trade_remedies_public/templates/static`;
const CSS_DIR = `${STATIC_DIR}/stylesheets`;
const CSS_FILES = `${CSS_DIR}/**/*.css`;
const CSS_MAPS = `${CSS_DIR}/**/*.css.map`;

const sassOptions = {
  // includePaths: ['./conf/'],
  outputStyle: "compressed",
};

gulp.task("clean", function () {
  return del([CSS_FILES, CSS_MAPS]);
});

gulp.task("sass:compile", function () {
  return gulp
    .src(SASS_MAIN)
    .pipe(sourcemaps.init())
    .pipe(sass(sassOptions))
    .pipe(sourcemaps.write("./maps"))
    .pipe(gulp.dest(CSS_DIR));
});

gulp.task("sass:watch", function () {
  gulp.watch([SASS_WATCH_FILES], gulp.series("sass:compile"));
});

gulp.task("sass", gulp.series("clean", "sass:compile"));

gulp.task("default", gulp.series(["sass"]));
